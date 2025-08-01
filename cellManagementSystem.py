import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import time
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Cell Management System",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-good {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 0.25rem;
        text-align: center;
        font-weight: bold;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.25rem;
        text-align: center;
        font-weight: bold;
    }
    .status-critical {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.25rem;
        text-align: center;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cells_data' not in st.session_state:
    st.session_state.cells_data = {}
if 'task_queue' not in st.session_state:
    st.session_state.task_queue = []
if 'system_logs' not in st.session_state:
    st.session_state.system_logs = []
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []

# Helper functions
def get_cell_status(cell_data):
    """Determine cell status based on parameters"""
    voltage = cell_data.get('voltage', 0)
    temp = cell_data.get('temp', 0)
    min_voltage = cell_data.get('min_voltage', 0)
    max_voltage = cell_data.get('max_voltage', 0)
    
    if voltage < min_voltage or voltage > max_voltage or temp > 45:
        return "Critical"
    elif temp > 35 or voltage < (min_voltage + 0.1):
        return "Warning"
    else:
        return "Good"

def generate_sample_data():
    """Generate sample cell data for demonstration"""
    sample_cells = {
        f"cell_1_lfp": {
            "voltage": 3.2,
            "current": 2.5,
            "temp": 28.5,
            "capacity": 8.0,
            "min_voltage": 2.8,
            "max_voltage": 3.6,
            "soc": 85,
            "cycle_count": 150
        },
        f"cell_2_nmc": {
            "voltage": 3.7,
            "current": 1.8,
            "temp": 32.1,
            "capacity": 6.66,
            "min_voltage": 3.2,
            "max_voltage": 4.0,
            "soc": 78,
            "cycle_count": 89
        }
    }
    st.session_state.cells_data.update(sample_cells)

def log_event(event_type, message):
    """Add event to system logs"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.system_logs.append({
        "timestamp": timestamp,
        "type": event_type,
        "message": message
    })

# Sidebar navigation
st.sidebar.title("🔋 Cell Management System")
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Setup", "Control Panel", "Task Manager", "Analytics"]
)

# Dashboard Page
if page == "Dashboard":
    st.title("📊 System Dashboard")
    
    if not st.session_state.cells_data:
        st.warning("No cells configured. Please go to Setup to add cells.")
        if st.button("Load Sample Data"):
            generate_sample_data()
            st.rerun()
    else:
        # System Overview Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_cells = len(st.session_state.cells_data)
        good_cells = sum(1 for cell in st.session_state.cells_data.values() 
                        if get_cell_status(cell) == "Good")
        warning_cells = sum(1 for cell in st.session_state.cells_data.values() 
                           if get_cell_status(cell) == "Warning")
        critical_cells = sum(1 for cell in st.session_state.cells_data.values() 
                            if get_cell_status(cell) == "Critical")
        
        with col1:
            st.metric("Total Cells", total_cells)
        with col2:
            st.metric("Healthy Cells", good_cells, delta=f"+{good_cells-warning_cells-critical_cells}")
        with col3:
            st.metric("Warning Cells", warning_cells, delta=f"-{warning_cells}" if warning_cells > 0 else None)
        with col4:
            st.metric("Critical Cells", critical_cells, delta=f"-{critical_cells}" if critical_cells > 0 else None)
        
        # Real-time Cell Status
        st.subheader("📈 Real-time Cell Status")
        
        # Create cell status dataframe
        status_data = []
        for cell_id, cell_data in st.session_state.cells_data.items():
            status_data.append({
                "Cell ID": cell_id,
                "Voltage (V)": cell_data.get('voltage', 0),
                "Current (A)": cell_data.get('current', 0),
                "Temperature (°C)": cell_data.get('temp', 0),
                "SOC (%)": cell_data.get('soc', 0),
                "Status": get_cell_status(cell_data)
            })
        
        df = pd.DataFrame(status_data)
        
        # Color code the status column
        def color_status(val):
            if val == "Good":
                return "background-color: #d4edda; color: #155724"
            elif val == "Warning":
                return "background-color: #fff3cd; color: #856404"
            else:
                return "background-color: #f8d7da; color: #721c24"
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # System Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Voltage chart
            fig_voltage = px.bar(df, x="Cell ID", y="Voltage (V)", 
                               title="Cell Voltages", color="Status",
                               color_discrete_map={"Good": "#28a745", "Warning": "#ffc107", "Critical": "#dc3545"})
            st.plotly_chart(fig_voltage, use_container_width=True)
        
        with col2:
            # Temperature chart
            fig_temp = px.bar(df, x="Cell ID", y="Temperature (°C)", 
                            title="Cell Temperatures", color="Status",
                            color_discrete_map={"Good": "#28a745", "Warning": "#ffc107", "Critical": "#dc3545"})
            st.plotly_chart(fig_temp, use_container_width=True)
        
        # System Logs
        st.subheader("📋 Recent System Logs")
        if st.session_state.system_logs:
            logs_df = pd.DataFrame(st.session_state.system_logs[-10:])  # Show last 10 logs
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No system logs available.")

# Setup Page
elif page == "Setup":
    st.title("⚙️ System Setup")
    
    tab1, tab2, tab3 = st.tabs(["Cell Configuration", "System Settings", "Import/Export"])
    
    with tab1:
        st.subheader("🔋 Add New Cell")
        
        col1, col2 = st.columns(2)
        with col1:
            cell_type = st.selectbox("Cell Type", ["lfp", "nmc", "nca", "lto"])
            cell_id = st.text_input("Cell ID", placeholder="e.g., cell_1_lfp")
        
        with col2:
            initial_voltage = 3.2 if cell_type == "lfp" else 3.6
            voltage = st.number_input("Initial Voltage (V)", value=initial_voltage, step=0.1)
            current = st.number_input("Current (A)", value=0.0, step=0.1)
        
        col3, col4 = st.columns(2)
        with col3:
            temp = st.number_input("Temperature (°C)", value=25.0, step=0.1)
            capacity = st.number_input("Capacity (Ah)", value=10.0, step=0.1)
        
        with col4:
            soc = st.number_input("State of Charge (%)", value=50, min_value=0, max_value=100)
            cycle_count = st.number_input("Cycle Count", value=0, step=1)
        
        if st.button("Add Cell", type="primary"):
            if cell_id:
                min_voltage = 2.8 if cell_type == "lfp" else 3.2
                max_voltage = 3.6 if cell_type == "lfp" else 4.0
                
                new_cell = {
                    "voltage": voltage,
                    "current": current,
                    "temp": temp,
                    "capacity": capacity,
                    "min_voltage": min_voltage,
                    "max_voltage": max_voltage,
                    "soc": soc,
                    "cycle_count": cycle_count,
                    "type": cell_type
                }
                
                st.session_state.cells_data[cell_id] = new_cell
                log_event("INFO", f"Cell {cell_id} added successfully")
                st.success(f"Cell {cell_id} added successfully!")
            else:
                st.error("Please enter a valid Cell ID")
        
        # Display existing cells
        if st.session_state.cells_data:
            st.subheader("📋 Configured Cells")
            for cell_id, cell_data in st.session_state.cells_data.items():
                with st.expander(f"{cell_id} - {cell_data.get('type', 'unknown').upper()}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Voltage:** {cell_data.get('voltage', 0)} V")
                        st.write(f"**Current:** {cell_data.get('current', 0)} A")
                    with col2:
                        st.write(f"**Temperature:** {cell_data.get('temp', 0)} °C")
                        st.write(f"**SOC:** {cell_data.get('soc', 0)} %")
                    with col3:
                        st.write(f"**Capacity:** {cell_data.get('capacity', 0)} Ah")
                        st.write(f"**Cycles:** {cell_data.get('cycle_count', 0)}")
                    
                    if st.button(f"Remove {cell_id}", key=f"remove_{cell_id}"):
                        del st.session_state.cells_data[cell_id]
                        log_event("WARNING", f"Cell {cell_id} removed")
                        st.rerun()
    
    with tab2:
        st.subheader("🔧 System Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Measurement Units", ["Metric", "Imperial"], index=0)
            st.number_input("Data Logging Interval (seconds)", value=10, min_value=1)
        
        with col2:
            st.selectbox("Temperature Scale", ["Celsius", "Fahrenheit"], index=0)
            st.checkbox("Enable Auto-shutdown on Critical", value=True)
        
        st.subheader("📊 Alert Thresholds")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("Max Temperature (°C)", value=45, step=1)
            st.number_input("Min Voltage Threshold", value=2.8, step=0.1)
        with col2:
            st.number_input("Max Current (A)", value=10.0, step=0.1)
            st.number_input("Max Voltage Threshold", value=4.2, step=0.1)
        with col3:
            st.number_input("Min SOC Warning (%)", value=20, step=1)
            st.number_input("Max SOC Warning (%)", value=90, step=1)
    
    with tab3:
        st.subheader("📥 Import Configuration")
        uploaded_file = st.file_uploader("Upload cell configuration", type=['json'])
        if uploaded_file:
            try:
                config = json.loads(uploaded_file.read())
                st.session_state.cells_data.update(config)
                st.success("Configuration imported successfully!")
            except Exception as e:
                st.error(f"Error importing configuration: {e}")
        
        st.subheader("📤 Export Configuration")
        if st.button("Export Current Configuration"):
            config_json = json.dumps(st.session_state.cells_data, indent=2)
            st.download_button(
                "Download Configuration",
                config_json,
                file_name="cell_config.json",
                mime="application/json"
            )

# Control Panel Page
elif page == "Control Panel":
    st.title("🎛️ Control Panel")
    
    if not st.session_state.cells_data:
        st.warning("No cells configured. Please go to Setup to add cells.")
    else:
        tab1, tab2, tab3 = st.tabs(["Cell Control", "Batch Operations", "Emergency Controls"])
        
        with tab1:
            st.subheader("🔋 Individual Cell Control")
            
            selected_cell = st.selectbox("Select Cell", list(st.session_state.cells_data.keys()))
            
            if selected_cell:
                cell_data = st.session_state.cells_data[selected_cell]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Current Status:**")
                    status = get_cell_status(cell_data)
                    if status == "Good":
                        st.markdown('<div class="status-good">GOOD</div>', unsafe_allow_html=True)
                    elif status == "Warning":
                        st.markdown('<div class="status-warning">WARNING</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="status-critical">CRITICAL</div>', unsafe_allow_html=True)
                
                with col2:
                    st.write("**Quick Actions:**")
                    if st.button("Reset Cell", key="reset_cell"):
                        # Reset cell to safe defaults
                        cell_data.update({"current": 0.0, "temp": 25.0})
                        log_event("INFO", f"Cell {selected_cell} reset")
                        st.success("Cell reset successfully!")
                
                # Manual parameter adjustment
                st.subheader("📊 Manual Parameter Control")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_voltage = st.number_input("Set Voltage (V)", 
                                                value=cell_data.get('voltage', 0), 
                                                step=0.01, key="manual_voltage")
                    new_current = st.number_input("Set Current (A)", 
                                                value=cell_data.get('current', 0), 
                                                step=0.1, key="manual_current")
                
                with col2:
                    new_temp = st.number_input("Set Temperature (°C)", 
                                             value=cell_data.get('temp', 0), 
                                             step=0.1, key="manual_temp")
                    new_soc = st.number_input("Set SOC (%)", 
                                            value=cell_data.get('soc', 0), 
                                            min_value=0, max_value=100, 
                                            key="manual_soc")
                
                with col3:
                    if st.button("Apply Changes", type="primary"):
                        cell_data.update({
                            "voltage": new_voltage,
                            "current": new_current,
                            "temp": new_temp,
                            "soc": new_soc
                        })
                        log_event("INFO", f"Manual parameters applied to {selected_cell}")
                        st.success("Parameters updated successfully!")
                        st.rerun()
        
        with tab2:
            st.subheader("🔄 Batch Operations")
            
            operation = st.selectbox("Select Operation", 
                                   ["Balance All Cells", "Emergency Stop All", "Reset All Temperatures", "Set All Currents to Zero"])
            
            if st.button("Execute Batch Operation", type="primary"):
                if operation == "Balance All Cells":
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        cell_data["current"] = 1.0  # Balancing current
                    log_event("INFO", "Batch balancing operation started")
                    st.success("All cells set to balancing mode!")
                
                elif operation == "Emergency Stop All":
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        cell_data["current"] = 0.0
                    log_event("WARNING", "Emergency stop - all cells stopped")
                    st.success("Emergency stop executed!")
                
                elif operation == "Reset All Temperatures":
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        cell_data["temp"] = 25.0
                    log_event("INFO", "All cell temperatures reset to 25°C")
                    st.success("All temperatures reset!")
                
                elif operation == "Set All Currents to Zero":
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        cell_data["current"] = 0.0
                    log_event("INFO", "All cell currents set to zero")
                    st.success("All currents set to zero!")
        
        with tab3:
            st.subheader("🚨 Emergency Controls")
            st.warning("Use these controls only in emergency situations!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🛑 EMERGENCY SHUTDOWN", type="primary"):
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        cell_data.update({"current": 0.0, "voltage": 0.0})
                    log_event("CRITICAL", "EMERGENCY SHUTDOWN ACTIVATED")
                    st.error("Emergency shutdown activated!")
            
            with col2:
                if st.button("🔄 SYSTEM RESTART"):
                    # Reset all cells to safe defaults
                    for cell_id, cell_data in st.session_state.cells_data.items():
                        if "lfp" in cell_id:
                            cell_data.update({"voltage": 3.2, "current": 0.0, "temp": 25.0})
                        else:
                            cell_data.update({"voltage": 3.6, "current": 0.0, "temp": 25.0})
                    log_event("INFO", "System restart completed")
                    st.success("System restarted successfully!")

# Task Manager Page
elif page == "Task Manager":
    st.title("📋 Task Manager")
    
    if not st.session_state.cells_data:
        st.warning("No cells configured. Please go to Setup to add cells.")
    else:
        tab1, tab2, tab3 = st.tabs(["Create Task", "Task Queue", "Task History"])
        
        with tab1:
            st.subheader("➕ Create New Task")
            
            col1, col2 = st.columns(2)
            with col1:
                task_type = st.selectbox("Task Type", ["CC_CV (Charge)", "CC_CD (Discharge)", "IDLE", "BALANCE"])
                target_cells = st.multiselect("Target Cells", list(st.session_state.cells_data.keys()))
            
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                scheduled_time = st.time_input("Schedule Time (optional)")
            
            # Task-specific parameters
            if task_type in ["CC_CV (Charge)", "CC_CD (Discharge)"]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    target_voltage = st.number_input("Target Voltage (V)", value=3.6, step=0.1)
                    target_current = st.number_input("Current (A)", value=1.0, step=0.1)
                with col2:
                    max_capacity = st.number_input("Max Capacity (Ah)", value=10.0, step=0.1)
                    max_temp = st.number_input("Max Temperature (°C)", value=45, step=1)
                with col3:
                    duration = st.number_input("Duration (minutes)", value=60, step=1)
                    cutoff_voltage = st.number_input("Cutoff Voltage (V)", value=2.8, step=0.1)
            
            elif task_type == "IDLE":
                duration = st.number_input("Idle Duration (minutes)", value=30, step=1)
            
            elif task_type == "BALANCE":
                balance_threshold = st.number_input("Balance Threshold (mV)", value=10, step=1)
                max_balance_current = st.number_input("Max Balance Current (A)", value=0.5, step=0.1)
            
            task_description = st.text_area("Task Description (optional)")
            
            if st.button("Create Task", type="primary"):
                if target_cells:
                    task = {
                        "id": f"task_{len(st.session_state.task_queue) + 1}",
                        "type": task_type,
                        "cells": target_cells,
                        "priority": priority,
                        "status": "Queued",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "description": task_description
                    }
                    
                    # Add task-specific parameters
                    if task_type in ["CC_CV (Charge)", "CC_CD (Discharge)"]:
                        task.update({
                            "target_voltage": target_voltage,
                            "current": target_current,
                            "max_capacity": max_capacity,
                            "max_temp": max_temp,
                            "duration": duration,
                            "cutoff_voltage": cutoff_voltage
                        })
                    elif task_type == "IDLE":
                        task["duration"] = duration
                    elif task_type == "BALANCE":
                        task.update({
                            "balance_threshold": balance_threshold,
                            "max_balance_current": max_balance_current
                        })
                    
                    st.session_state.task_queue.append(task)
                    log_event("INFO", f"Task {task['id']} created for cells: {', '.join(target_cells)}")
                    st.success(f"Task {task['id']} created successfully!")
                else:
                    st.error("Please select at least one target cell.")
        
        with tab2:
            st.subheader("📋 Task Queue")
            
            if st.session_state.task_queue:
                # Control buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("▶️ Start Next Task"):
                        if st.session_state.task_queue:
                            next_task = st.session_state.task_queue[0]
                            next_task["status"] = "Running"
                            log_event("INFO", f"Task {next_task['id']} started")
                            st.success(f"Started task: {next_task['id']}")
                
                with col2:
                    if st.button("⏸️ Pause All Tasks"):
                        for task in st.session_state.task_queue:
                            if task["status"] == "Running":
                                task["status"] = "Paused"
                        log_event("WARNING", "All running tasks paused")
                        st.info("All running tasks have been paused.")
                
                with col3:
                    if st.button("🗑️ Clear Completed"):
                        st.session_state.task_queue = [t for t in st.session_state.task_queue if t["status"] != "Completed"]
                        st.success("Completed tasks cleared.")
                
                # Task queue table
                queue_data = []
                for task in st.session_state.task_queue:
                    queue_data.append({
                        "Task ID": task["id"],
                        "Type": task["type"],
                        "Cells": ", ".join(task["cells"]),
                        "Priority": task["priority"],
                        "Status": task["status"],
                        "Created": task["created"]
                    })
                
                df_queue = pd.DataFrame(queue_data)
                st.dataframe(df_queue, use_container_width=True)
                
                # Task details
                if queue_data:
                    selected_task_id = st.selectbox("Select task for details", [t["Task ID"] for t in queue_data])
                    selected_task = next((t for t in st.session_state.task_queue if t["id"] == selected_task_id), None)
                    
                    if selected_task:
                        with st.expander(f"Task Details: {selected_task_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Type:** {selected_task['type']}")
                                st.write(f"**Status:** {selected_task['status']}")
                                st.write(f"**Priority:** {selected_task['priority']}")
                            with col2:
                                st.write(f"**Target Cells:** {', '.join(selected_task['cells'])}")
                                st.write(f"**Created:** {selected_task['created']}")
                            
                            if selected_task.get('description'):
                                st.write(f"**Description:** {selected_task['description']}")
                            
                            # Task control buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("▶️ Start", key=f"start_{selected_task_id}"):
                                    selected_task["status"] = "Running"
                                    st.rerun()
                            with col2:
                                if st.button("⏸️ Pause", key=f"pause_{selected_task_id}"):
                                    selected_task["status"] = "Paused"
                                    st.rerun()
                            with col3:
                                if st.button("❌ Cancel", key=f"cancel_{selected_task_id}"):
                                    st.session_state.task_queue.remove(selected_task)
                                    log_event("WARNING", f"Task {selected_task_id} cancelled")
                                    st.rerun()
            else:
                st.info("No tasks in queue. Create a new task to get started.")
        
        with tab3:
            st.subheader("📚 Task History")
            # This would show completed tasks in a real implementation
            st.info("Task history feature will show completed and cancelled tasks.")

# Analytics Page
elif page == "Analytics":
    st.title("📊 Analytics & Reports")
    
    if not st.session_state.cells_data:
        st.warning("No cells configured. Please go to Setup to add cells.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Performance Overview", "Trends Analysis", "Health Monitoring", "Reports"])
        
        with tab1:
            st.subheader("📈 Performance Overview")
            
            # Generate sample historical data for demonstration
            if st.button("Generate Sample Historical Data"):
                dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='H')
                for cell_id in st.session_state.cells_data.keys():
                    for date in dates[-100:]:  # Last 100 hours
                        st.session_state.historical_data.append({
                            "timestamp": date,
                            "cell_id": cell_id,
                            "voltage": random.uniform(3.0, 4.0),
                            "current": random.uniform(0, 5),
                            "temperature": random.uniform(20, 40),
                            "soc": random.uniform(20, 90)
                        })
                st.success("Sample historical data generated!")
            
            if st.session_state.historical_data:
                df_hist = pd.DataFrame(st.session_state.historical_data)
                
                # Time series charts
                selected_metric = st.selectbox("Select Metric", ["voltage", "current", "temperature", "soc"])
                
                fig = px.line(df_hist, x="timestamp", y=selected_metric, color="cell_id",
                            title=f"{selected_metric.title()} Over Time")
                st.plotly_chart(fig, use_container_width=True)
                
                # Performance metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_voltage = df_hist["voltage"].mean()
                    st.metric("Avg Voltage", f"{avg_voltage:.2f} V")
                with col2:
                    avg_current = df_hist["current"].mean()
                    st.metric("Avg Current", f"{avg_current:.2f} A")
                with col3:
                    avg_temp = df_hist["temperature"].mean()
                    st.metric("Avg Temperature", f"{avg_temp:.1f} °C")
                with col4:
                    avg_soc = df_hist["soc"].mean()
                    st.metric("Avg SOC", f"{avg_soc:.1f} %")
        
        with tab2:
            st.subheader("📊 Trends Analysis")
            
            if st.session_state.historical_data:
                df_hist = pd.DataFrame(st.session_state.historical_data)
                
                # Correlation analysis
                st.subheader("🔗 Parameter Correlations")
                correlation_data = df_hist[["voltage", "current", "temperature", "soc"]].corr()
                
                fig_corr = px.imshow(correlation_data, 
                                   title="Parameter Correlation Matrix",
                                   color_continuous_scale="RdBu_r",
                                   aspect="auto")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Trend analysis by cell
                st.subheader("📈 Individual Cell Trends")
                selected_cell = st.selectbox("Select Cell for Detailed Analysis", 
                                           df_hist["cell_id"].unique())
                
                cell_data = df_hist[df_hist["cell_id"] == selected_cell]
                
                # Create subplots for multiple metrics
                fig_trends = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=("Voltage", "Current", "Temperature", "SOC"),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                fig_trends.add_trace(
                    go.Scatter(x=cell_data["timestamp"], y=cell_data["voltage"], name="Voltage"),
                    row=1, col=1
                )
                fig_trends.add_trace(
                    go.Scatter(x=cell_data["timestamp"], y=cell_data["current"], name="Current"),
                    row=1, col=2
                )
                fig_trends.add_trace(
                    go.Scatter(x=cell_data["timestamp"], y=cell_data["temperature"], name="Temperature"),
                    row=2, col=1
                )
                fig_trends.add_trace(
                    go.Scatter(x=cell_data["timestamp"], y=cell_data["soc"], name="SOC"),
                    row=2, col=2
                )
                
                fig_trends.update_layout(height=600, title_text=f"Detailed Trends for {selected_cell}")
                st.plotly_chart(fig_trends, use_container_width=True)
                
                # Statistical summary
                st.subheader("📋 Statistical Summary")
                summary_stats = cell_data[["voltage", "current", "temperature", "soc"]].describe()
                st.dataframe(summary_stats, use_container_width=True)
            else:
                st.info("No historical data available. Generate sample data to see trends.")
        
        with tab3:
            st.subheader("🏥 Health Monitoring")
            
            # Cell health scoring algorithm
            health_scores = {}
            for cell_id, cell_data in st.session_state.cells_data.items():
                voltage = cell_data.get('voltage', 0)
                temp = cell_data.get('temp', 0)
                cycle_count = cell_data.get('cycle_count', 0)
                soc = cell_data.get('soc', 0)
                
                # Simple health scoring (0-100)
                voltage_score = 100 if 3.0 <= voltage <= 4.0 else max(0, 100 - abs(voltage - 3.5) * 50)
                temp_score = 100 if temp <= 35 else max(0, 100 - (temp - 35) * 5)
                cycle_score = max(0, 100 - (cycle_count / 1000) * 100)  # Assuming 1000 cycles = 0% health
                soc_score = 100 if 20 <= soc <= 80 else max(0, 100 - abs(soc - 50) * 2)
                
                overall_health = (voltage_score + temp_score + cycle_score + soc_score) / 4
                health_scores[cell_id] = {
                    "overall": overall_health,
                    "voltage": voltage_score,
                    "temperature": temp_score,
                    "cycles": cycle_score,
                    "soc": soc_score
                }
            
            # Health overview
            st.subheader("🎯 Health Overview")
            health_data = []
            for cell_id, scores in health_scores.items():
                health_data.append({
                    "Cell ID": cell_id,
                    "Overall Health": f"{scores['overall']:.1f}%",
                    "Voltage Health": f"{scores['voltage']:.1f}%",
                    "Temp Health": f"{scores['temperature']:.1f}%",
                    "Cycle Health": f"{scores['cycles']:.1f}%",
                    "SOC Health": f"{scores['soc']:.1f}%"
                })
            
            df_health = pd.DataFrame(health_data)
            st.dataframe(df_health, use_container_width=True)
            
            # Health distribution chart
            overall_scores = [scores['overall'] for scores in health_scores.values()]
            fig_health = px.histogram(x=overall_scores, nbins=10, 
                                    title="Health Score Distribution",
                                    labels={"x": "Health Score (%)", "y": "Number of Cells"})
            st.plotly_chart(fig_health, use_container_width=True)
            
            # Predictive maintenance alerts
            st.subheader("⚠️ Maintenance Alerts")
            alerts = []
            for cell_id, scores in health_scores.items():
                if scores['overall'] < 70:
                    alerts.append(f"🔴 {cell_id}: Overall health below 70% - Schedule maintenance")
                elif scores['overall'] < 85:
                    alerts.append(f"🟡 {cell_id}: Overall health below 85% - Monitor closely")
                
                if scores['cycles'] < 50:
                    alerts.append(f"🔄 {cell_id}: High cycle count - Consider replacement")
                
                if scores['temperature'] < 80:
                    alerts.append(f"🌡️ {cell_id}: Temperature concerns - Check cooling system")
            
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.success("✅ All cells are in good health!")
        
        with tab4:
            st.subheader("📄 Reports & Export")
            
            # Report generation options
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Generate Reports")
                report_type = st.selectbox("Report Type", 
                                         ["System Status", "Performance Summary", "Health Report", "Task History"])
                
                date_range = st.date_input("Report Date Range", 
                                         value=[datetime.now().date() - timedelta(days=7), 
                                               datetime.now().date()],
                                         max_value=datetime.now().date())
                
                include_charts = st.checkbox("Include Charts", value=True)
                
                if st.button("Generate Report", type="primary"):
                    # Generate report based on type
                    report_data = {
                        "report_type": report_type,
                        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "date_range": f"{date_range[0]} to {date_range[1] if len(date_range) > 1 else date_range[0]}",
                        "total_cells": len(st.session_state.cells_data),
                        "cells_data": st.session_state.cells_data,
                        "system_logs": st.session_state.system_logs[-50:],  # Last 50 logs
                        "task_queue": st.session_state.task_queue
                    }
                    
                    # Convert to JSON for download
                    report_json = json.dumps(report_data, indent=2, default=str)
                    
                    st.download_button(
                        f"Download {report_type} Report",
                        report_json,
                        file_name=f"{report_type.lower().replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                    st.success(f"{report_type} report generated successfully!")
            
            with col2:
                st.subheader("📊 Data Export")
                
                export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])
                
                data_to_export = st.multiselect("Data to Export", 
                                               ["Cell Data", "System Logs", "Task Queue", "Historical Data"])
                
                if st.button("Export Data"):
                    export_data = {}
                    
                    if "Cell Data" in data_to_export:
                        export_data["cells"] = st.session_state.cells_data
                    
                    if "System Logs" in data_to_export:
                        export_data["logs"] = st.session_state.system_logs
                    
                    if "Task Queue" in data_to_export:
                        export_data["tasks"] = st.session_state.task_queue
                    
                    if "Historical Data" in data_to_export:
                        export_data["historical"] = st.session_state.historical_data
                    
                    if export_format == "JSON":
                        export_json = json.dumps(export_data, indent=2, default=str)
                        st.download_button(
                            "Download JSON Export",
                            export_json,
                            file_name=f"cell_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    elif export_format == "CSV":
                        # Convert cell data to CSV format
                        if "Cell Data" in data_to_export:
                            cells_df = pd.DataFrame.from_dict(st.session_state.cells_data, orient='index')
                            csv_data = cells_df.to_csv()
                            st.download_button(
                                "Download CSV Export",
                                csv_data,
                                file_name=f"cell_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    
                    st.success("Data export prepared!")
            
            # Quick statistics
            st.subheader("📈 Quick Statistics")
            if st.session_state.cells_data:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_capacity = sum(cell.get('capacity', 0) for cell in st.session_state.cells_data.values())
                    st.metric("Total Capacity", f"{total_capacity:.1f} Ah")
                
                with col2:
                    avg_soc = sum(cell.get('soc', 0) for cell in st.session_state.cells_data.values()) / len(st.session_state.cells_data)
                    st.metric("Average SOC", f"{avg_soc:.1f}%")
                
                with col3:
                    total_cycles = sum(cell.get('cycle_count', 0) for cell in st.session_state.cells_data.values())
                    st.metric("Total Cycles", f"{total_cycles:,}")
                
                with col4:
                    active_tasks = sum(1 for task in st.session_state.task_queue if task.get('status') == 'Running')
                    st.metric("Active Tasks", active_tasks)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🔋 Cell Management System v1.0 | Built with Streamlit | 
        Last Updated: {}
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)

# Auto-refresh for real-time data (optional)
if st.sidebar.checkbox("Auto-refresh (10s)", value=False):
    time.sleep(10)
    st.rerun()