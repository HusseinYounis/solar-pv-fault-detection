import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _time_to_day_fraction(timestamp_text: str) -> float:
    parsed = datetime.strptime(timestamp_text, '%H:%M:%S')
    return (parsed.hour * 3600 + parsed.minute * 60 + parsed.second) / 86400.0


def _predict_transformer_expected_power(
    history_df: pd.DataFrame,
    temperature: float,
    irradiance: float,
    context_length: int,
    train_steps: int,
) -> tuple[float | None, str | None]:
    try:
        import torch
        from transformers import TimeSeriesTransformerConfig, TimeSeriesTransformerForPrediction
    except ImportError:
        return None, "Transformer forecast requires installing packages: pip install transformers torch"

    if train_steps < 1:
        return None, "Training steps must be at least 1."

    working_df = history_df.copy()
    working_df['Expected_Power'] = pd.to_numeric(working_df['Expected_Power'], errors='coerce')
    working_df['Temperature'] = pd.to_numeric(working_df['Temperature'], errors='coerce')
    working_df['Irradiance'] = pd.to_numeric(working_df['Irradiance'], errors='coerce')
    working_df = working_df.dropna(subset=['Expected_Power', 'Temperature', 'Irradiance'])

    prediction_length = 1
    lags_sequence = [1]
    max_lag = max(lags_sequence)
    required_past_length = context_length + max_lag
    min_required_rows = required_past_length + prediction_length

    if len(working_df) < min_required_rows:
        return None, f"Need at least {min_required_rows} valid history rows for transformer forecasting."

    powers = working_df['Expected_Power'].to_numpy(dtype=np.float32)
    temperatures = working_df['Temperature'].to_numpy(dtype=np.float32) / 75.0
    irradiances = working_df['Irradiance'].to_numpy(dtype=np.float32) / 1200.0
    time_features = np.array(
        [_time_to_day_fraction(value) for value in working_df['Timestamp'].astype(str).tolist()],
        dtype=np.float32,
    )

    feature_matrix = np.stack([time_features, temperatures, irradiances], axis=1).astype(np.float32)
    window_count = len(working_df) - required_past_length
    if window_count < 1:
        return None, "Not enough history windows for transformer training."

    past_values = []
    past_time_features = []
    past_observed_mask = []
    future_values = []
    future_time_features = []

    for start_idx in range(window_count):
        end_idx = start_idx + required_past_length
        past_values.append(powers[start_idx:end_idx])
        past_time_features.append(feature_matrix[start_idx:end_idx, :])
        past_observed_mask.append(np.ones(required_past_length, dtype=np.float32))
        future_values.append([powers[end_idx]])
        future_time_features.append([feature_matrix[end_idx, :]])

    past_values_tensor = torch.tensor(np.array(past_values), dtype=torch.float32)
    past_time_features_tensor = torch.tensor(np.array(past_time_features), dtype=torch.float32)
    past_observed_mask_tensor = torch.tensor(np.array(past_observed_mask), dtype=torch.float32)
    future_values_tensor = torch.tensor(np.array(future_values), dtype=torch.float32)
    future_time_features_tensor = torch.tensor(np.array(future_time_features), dtype=torch.float32)

    config = TimeSeriesTransformerConfig(
        prediction_length=prediction_length,
        context_length=context_length,
        lags_sequence=lags_sequence,
        input_size=1,
        num_time_features=3,
        encoder_layers=2,
        decoder_layers=2,
        d_model=32,
        encoder_ffn_dim=64,
        decoder_ffn_dim=64,
        encoder_attention_heads=2,
        decoder_attention_heads=2,
        dropout=0.1,
        num_parallel_samples=50,
    )

    model = TimeSeriesTransformerForPrediction(config)
    optimizer = torch.optim.Adam(model.parameters(), lr=5e-4)
    model.train()

    for _ in range(train_steps):
        optimizer.zero_grad()
        outputs = model(
            past_values=past_values_tensor,
            past_time_features=past_time_features_tensor,
            past_observed_mask=past_observed_mask_tensor,
            future_values=future_values_tensor,
            future_time_features=future_time_features_tensor,
        )
        outputs.loss.backward()
        optimizer.step()

    latest_time_feature = np.array(
        [_time_to_day_fraction(datetime.now().strftime('%H:%M:%S')), temperature / 75.0, irradiance / 1200.0],
        dtype=np.float32,
    )

    inference_past_values = torch.tensor(powers[-required_past_length:], dtype=torch.float32).unsqueeze(0)
    inference_past_time_features = torch.tensor(feature_matrix[-required_past_length:, :], dtype=torch.float32).unsqueeze(0)
    inference_mask = torch.ones((1, required_past_length), dtype=torch.float32)
    inference_future_time_features = torch.tensor(latest_time_feature, dtype=torch.float32).reshape(1, 1, 3)

    model.eval()
    with torch.no_grad():
        prediction_output = model.generate(
            past_values=inference_past_values,
            past_time_features=inference_past_time_features,
            past_observed_mask=inference_mask,
            future_time_features=inference_future_time_features,
        )

    forecast_samples = prediction_output.sequences
    point_forecast = float(forecast_samples.median(dim=-1).values[0, 0].item())
    return max(0.0, point_forecast), None


def render_dashboard() -> None:
    # --- 1. Page Configuration & Layout ---
    st.set_page_config(page_title="Intelligent PV Fault Simulation Dashboard", layout="wide")
    st.title("☀️ Autonomous Solar System Fault Diagnosis & Simulation Field")
    st.markdown("Use the controls below to dynamically adjust environment parameters, simulate faults, and view AI-ready diagnostic results.")

    # --- 2. Initialize Session State for Data History ---
    if 'history_df' not in st.session_state:
        st.session_state.history_df = pd.DataFrame(columns=['Timestamp', 'Irradiance', 'Temperature', 'Tilt_Angle', 'Actual_Voltage', 'Actual_Current', 'Actual_Power', 'Expected_Power', 'Status'])
    if 'live_updates_enabled' not in st.session_state:
        st.session_state.live_updates_enabled = False
    if 'live_update_step' not in st.session_state:
        st.session_state.live_update_step = 0

    # --- 3. Sidebar: Environment Controls & Fault Toggles ---
    st.sidebar.header("🛠️ Environmental & Structural Control")
    irradiance = st.sidebar.slider("Solar Irradiance (W/m²)", min_value=0, max_value=1200, value=900, step=50)
    temperature = st.sidebar.slider("Panel Temperature (°C)", min_value=10, max_value=75, value=35, step=1)
    panel_angle = st.sidebar.slider("Panel Physical Tilt Angle (°)", min_value=0, max_value=90, value=30, step=5)
    optimal_angle = st.sidebar.slider("Theoretical Optimal Sun Angle (°)", min_value=0, max_value=90, value=30, step=5)

    st.sidebar.markdown("---")
    st.sidebar.header("💥 Fault & Degradation Injectors")
    dust_percentage = st.sidebar.slider("Dust & Soiling Accumulation (%)", min_value=0, max_value=100, value=0, step=5)
    fault_selection = st.sidebar.radio(
        "Select System Status / Fault Mode:",
        options=["Normal Operations", "Simulate Short Circuit", "Simulate Open Circuit"]
    )
    st.sidebar.markdown("---")
    st.sidebar.header("🧠 Transformer Forecast")
    use_transformer_forecast = st.sidebar.checkbox("Enable Time-Series Transformer expected power", value=False)
    transformer_mode = st.sidebar.radio(
        "Transformer run mode",
        options=["Unlimited", "Max steps"],
        index=1,
        disabled=not use_transformer_forecast,
    )
    transformer_max_steps = st.sidebar.slider(
        "Transformer max steps",
        min_value=5,
        max_value=120,
        value=30,
        step=5,
        disabled=(not use_transformer_forecast or transformer_mode == "Unlimited"),
    )
    transformer_context_length = st.sidebar.slider(
        "Transformer context length",
        min_value=4,
        max_value=20,
        value=8,
        step=1,
        disabled=not use_transformer_forecast,
    )

    # --- 4. Mathematical Modeling & AI/Logic Analysis Engine ---
    # Theoretical baseline calculations (Ideal values for your prototype cell size)
    V_ideal_oc = 18.0  # Open circuit voltage baseline
    I_ideal_sc = 1.5   # Short circuit current baseline

    # Temperature drag coefficient (Silicon panels drop efficiency as they heat up)
    temp_coefficient = 1.0 - (temperature - 25) * 0.004

    # Angle misalignment loss calculation
    angle_deviation = abs(panel_angle - optimal_angle)
    angle_efficiency = np.cos(np.radians(angle_deviation))

    # Dust reduction factor
    dust_factor = (100 - dust_percentage) / 100.0

    # Calculate expected ideal baseline power output
    expected_voltage = V_ideal_oc * temp_coefficient
    expected_current = I_ideal_sc * (irradiance / 1000.0)
    expected_power = expected_voltage * expected_current * angle_efficiency

    # Calculate live/actual output based on injected fault parameters
    actual_voltage = expected_voltage
    actual_current = expected_current * dust_factor * angle_efficiency

    # Inject chosen fault patterns into the telemetry
    status_message = "🟢 System Healthy"
    status_color = "green"

    if fault_selection == "Simulate Short Circuit":
        actual_voltage = 0.1  # Volts drop to near zero
        actual_current = I_ideal_sc * 1.2  # High bypass current
        status_message = "💥 Short Circuit Fault Detected!"
        status_color = "red"
    elif fault_selection == "Simulate Open Circuit":
        actual_voltage = V_ideal_oc * temp_coefficient  # Voltage reads open circuit max
        actual_current = 0.0  # Current drops to absolute zero
        status_message = "🔌 Open Circuit / Cable Cut Detected!"
        status_color = "red"
    elif dust_percentage >= 25:
        status_message = "🍃 High Dust & Soiling Accumulation Warning!"
        status_color = "orange"
    elif angle_deviation >= 20:
        status_message = "📐 Panel Tilt Angle Adjustment Required"
        status_color = "orange"

    actual_power = actual_voltage * actual_current

    transformer_expected_power = None
    transformer_error = None
    if use_transformer_forecast:
        transformer_steps = 30 if transformer_mode == "Unlimited" else transformer_max_steps
        transformer_expected_power, transformer_error = _predict_transformer_expected_power(
            history_df=st.session_state.history_df if 'history_df' in st.session_state else pd.DataFrame(),
            temperature=temperature,
            irradiance=irradiance,
            context_length=transformer_context_length,
            train_steps=transformer_steps,
        )

    # --- 5. Main Dashboard KPIs ---
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    with kpi_col1:
        st.metric("Live Voltage", f"{actual_voltage:.2f} V")
    with kpi_col2:
        st.metric("Live Current", f"{actual_current:.2f} A")
    with kpi_col3:
        st.metric("Actual Power Output", f"{actual_power:.2f} W")
    with kpi_col4:
        st.metric("Expected Yield Power", f"{expected_power:.2f} W")
    with kpi_col5:
        if transformer_expected_power is not None:
            st.metric("Transformer Expected Power", f"{transformer_expected_power:.2f} W")
        else:
            st.metric("Transformer Expected Power", "N/A")

    st.markdown(f"### Diagnostic Assessment: :{status_color}[{status_message}]")
    if transformer_error is not None:
        st.warning(transformer_error)

    # --- 6. Logging & Appending Data to History ---
    current_time = datetime.now().strftime('%H:%M:%S')
    new_log = pd.DataFrame([{
        'Timestamp': current_time,
        'Irradiance': irradiance,
        'Temperature': temperature,
        'Tilt_Angle': panel_angle,
        'Actual_Voltage': actual_voltage,
        'Actual_Current': actual_current,
        'Actual_Power': actual_power,
        'Expected_Power': expected_power,
        'Status': status_message
    }])

    st.session_state.history_df = pd.concat([st.session_state.history_df, new_log], ignore_index=True)
    # Keep only the last 30 data points for real-time tracking smoothness
    if len(st.session_state.history_df) > 30:
        st.session_state.history_df = st.session_state.history_df.iloc[1:].reset_index(drop=True)

    # --- 7. Plotting Dynamic Charts via Plotly ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📈 Electrical Characteristics Comparison")
        fig_electrical = go.Figure()
        fig_electrical.add_trace(go.Scatter(x=st.session_state.history_df['Timestamp'], y=st.session_state.history_df['Actual_Voltage'], name='Voltage (V)', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
        fig_electrical.add_trace(go.Scatter(x=st.session_state.history_df['Timestamp'], y=st.session_state.history_df['Actual_Current'], name='Current (A)', mode='lines+markers', line=dict(color='#ff7f0e', width=2)))
        fig_electrical.update_layout(xaxis_title="Timeline", yaxis_title="Sensor Values", margin=dict(l=20, r=20, t=30, b=20), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_electrical, use_container_width=True)

    with chart_col2:
        st.subheader("⚡ System Efficiency: Actual vs Expected Power")
        fig_power = go.Figure()
        fig_power.add_trace(go.Scatter(x=st.session_state.history_df['Timestamp'], y=st.session_state.history_df['Actual_Power'], name='Actual Power (W)', mode='lines+markers', fill='tozeroy', line=dict(color='#2ca02c')))
        fig_power.add_trace(go.Scatter(x=st.session_state.history_df['Timestamp'], y=st.session_state.history_df['Expected_Power'], name='Expected Power (W)', mode='lines', line=dict(color='#d62728', dash='dash')))
        if transformer_expected_power is not None:
            latest_timestamp = st.session_state.history_df['Timestamp'].iloc[-1]
            fig_power.add_trace(go.Scatter(x=[latest_timestamp], y=[transformer_expected_power], name='Transformer Expected (W)', mode='markers', marker=dict(color='#9467bd', size=12, symbol='diamond')))
        fig_power.update_layout(xaxis_title="Timeline", yaxis_title="Power (Watts)", margin=dict(l=20, r=20, t=30, b=20), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_power, use_container_width=True)

    # --- 8. Historic Logs Data Table ---
    st.subheader("📋 Historical Database Registry")
    st.dataframe(st.session_state.history_df.iloc[::-1], use_container_width=True)

    # --- 9. Auto-Refresh Loop Emulation ---
    # Creates a small trigger interval to seamlessly append data over time
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Live Update Control")

    run_mode = st.sidebar.radio(
        "Run mode",
        options=["Unlimited", "Max steps"],
        index=1
    )
    max_steps = int(
        st.sidebar.slider(
            "Max steps",
            min_value=1,
            max_value=300,
            value=10,
            step=1,
            disabled=(run_mode == "Unlimited")
        )
    )
    update_interval_seconds = 1

    toggle_label = "Stop Live Sensor Updates" if st.session_state.live_updates_enabled else "Start Live Sensor Updates"
    if st.sidebar.button(toggle_label):
        st.session_state.live_updates_enabled = not st.session_state.live_updates_enabled
        if st.session_state.live_updates_enabled:
            st.session_state.live_update_step = 0
            st.toast("Live updates enabled.", icon="🟢")
        else:
            st.toast("Live updates stopped.", icon="⏹️")

    status_text = "ON" if st.session_state.live_updates_enabled else "OFF"
    st.sidebar.caption(f"Status: {status_text}")
    if run_mode == "Unlimited":
        st.sidebar.caption(f"Step: {st.session_state.live_update_step} (unlimited)")
    else:
        st.sidebar.caption(f"Step: {st.session_state.live_update_step}/{max_steps}")
    st.sidebar.caption(f"Update every: {update_interval_seconds} second(s)")

    if st.session_state.live_updates_enabled:
        if run_mode == "Unlimited":
            st.session_state.live_update_step += 1
            time.sleep(update_interval_seconds)
            st.rerun()
        else:
            if st.session_state.live_update_step < max_steps:
                st.session_state.live_update_step += 1
                time.sleep(update_interval_seconds)
                st.rerun()
            else:
                st.session_state.live_updates_enabled = False
                st.toast("Live update cycle completed.", icon="✅")


def main() -> None:
    render_dashboard()


if __name__ == "__main__":
    main()
