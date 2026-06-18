within DHN_Benchmark.Components;
model PlantStation
  "Ideal central heat plant for 3GDH benchmark networks.
   Comprises an expansion vessel (absolute pressure reference),
   a variable-speed primary circulation pump (constant differential-pressure
   control), and an ideal heater that imposes the district supply temperature.
   The model exposes two fluid ports (supply outlet and return inlet) and
   two output signals (supplied thermal power and total mass flow rate)
   for benchmark post-processing.
  "
  
  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

  // ---------------------------------------------------------------
  // Design parameters
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.Temperature TDisSup_nominal = 273.15 + 80
    "Nominal district supply temperature [K]";

  parameter Modelica.Units.SI.MassFlowRate mDis_flow_nominal = 1.3905
    "Nominal total mass flow rate leaving the plant [kg/s]";

  parameter Modelica.Units.SI.HeatFlowRate QDis_flow_nominal = 210000
    "Nominal plant heating capacity (includes safety margin) [W]";

  parameter Modelica.Units.SI.Pressure p_exp = 1000000
    "Absolute pressure at expansion vessel (= pump supply pressure) [Pa]";

  parameter Modelica.Units.SI.PressureDifference dp_pump_nominal = 800000
    "Nominal pump differential pressure [Pa]";

  parameter Modelica.Units.SI.PressureDifference dp_pump_set = 800000
    "Differential pressure setpoint for constant-dP pump control [Pa]";

  parameter Modelica.Units.SI.PressureDifference dp_heater_nominal = 10000
    "Nominal pressure drop across the ideal heater [Pa]";
    
  // ---------------------------------------------------------------
  // Expansion vessel (absolute pressure reference)
  // ---------------------------------------------------------------
  Buildings.Fluid.Sources.Boundary_pT exp(
    redeclare package Medium = Medium,
    p      = p_exp,
    T      = TDisSup_nominal,
    nPorts = 1)
    "Expansion vessel — sets absolute pressure reference for the primary loop"annotation(
    Placement(transformation(origin = {-80, -40}, extent = {{-10, -10}, {10, 10}})));

  // ---------------------------------------------------------------
  // Primary circulation pump
  // ---------------------------------------------------------------
  Buildings.Fluid.Movers.FlowControlled_dp pump(
    redeclare package Medium = Medium,
    m_flow_nominal  = mDis_flow_nominal,
    dp_nominal      = dp_pump_nominal,
    inputType       = Buildings.Fluid.Types.InputType.Continuous,
    addPowerToMedium = false)
    "Primary circulation pump (constant differential-pressure control)" annotation(
    Placement(transformation(origin = {-20, -40}, extent = {{-10, -10}, {10, 10}})));
  
  Modelica.Blocks.Sources.Constant dpPumpSet(k = dp_pump_set)
     "Differential pressure setpoint [Pa]" annotation(
    Placement(transformation(origin = {-70, 20}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // Ideal heater (imposes district supply temperature)
  // ---------------------------------------------------------------
  Buildings.Fluid.HeatExchangers.Heater_T plaHea(
    redeclare package Medium = Medium,
    m_flow_nominal = mDis_flow_nominal,
    dp_nominal     = dp_heater_nominal,
    QMax_flow      = QDis_flow_nominal)
    "Ideal central plant heater (imposes supply temperature)" annotation(
    Placement(transformation(origin = {40, -40}, extent = {{-10, -10}, {10, 10}})));
  
  Modelica.Blocks.Sources.Constant TPlantSup(k = TDisSup_nominal)
    "Plant supply temperature setpoint signal [K]" annotation(
    Placement(transformation(origin = {-70, 60}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // Instrumentation sensor — return temperature
  // ---------------------------------------------------------------
  Buildings.Fluid.Sensors.TemperatureTwoPort senT_ret(
    redeclare package Medium = Medium,
    m_flow_nominal    = mDis_flow_nominal,
    allowFlowReversal = false,
    tau               = 0)
    "Return temperature after pump, before heat exchanger [K]" annotation(
    Placement(transformation(origin = {10, -40}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // External fluid ports
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_b port_bDis(
    redeclare package Medium = Medium)
    "District supply outlet (to network)" annotation(
    Placement(transformation(origin = {100, 20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {100, 20}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_a port_aDis(
    redeclare package Medium = Medium)
    "District return inlet (from network)" annotation(
    Placement(transformation(origin = {100, -20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {100, -20}, extent = {{-10, -10}, {10, 10}})));

  // ---------------------------------------------------------------
  // Output signals
  // ---------------------------------------------------------------
  Modelica.Blocks.Interfaces.RealOutput Q_flow
    "Thermal power delivered by the plant [W]" annotation(
    Placement(transformation(origin = {110, 70}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {110, 70}, extent = {{-10, -10}, {10, 10}})));

equation

  // ---------------------------------------------------------------
  // Primary loop connections
  // ---------------------------------------------------------------
  connect(exp.ports[1], pump.port_a) annotation(
    Line(points = {{-70, -40}, {-30, -40}}, color = {0, 127, 255}));
  connect(port_aDis, pump.port_a) annotation(
    Line(points = {{100, -20}, {-40, -20}, {-40, -40}, {-30, -40}}));
    connect(pump.port_b, senT_ret.port_a) annotation(
    Line(points = {{-10, -40}, {0, -40}}, color = {0, 127, 255}));
  connect(senT_ret.port_b, plaHea.port_a) annotation(
    Line(points = {{20, -40}, {30, -40}}, color = {0, 127, 255}));  

  connect(plaHea.port_b, port_bDis) annotation(
    Line(points = {{50, -40}, {60, -40}, {60, 20}, {100, 20}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Control signal connections
  // ---------------------------------------------------------------
  connect(dpPumpSet.y, pump.dp_in) annotation(
    Line(points = {{-58, 20}, {-20, 20}, {-20, -28}}, color = {0, 0, 127}));
  connect(TPlantSup.y, plaHea.TSet) annotation(
    Line(points = {{-58, 60}, {20, 60}, {20, -32}, {28, -32}}, color = {0, 0, 127}));
  
  // ---------------------------------------------------------------
  // Output signal connections
  // ---------------------------------------------------------------
  connect(plaHea.Q_flow, Q_flow) annotation(
    Line(points = {{52, -32}, {80, -32}, {80, 70}, {110, 70}}, color = {0, 0, 127}));

annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    Icon(
      coordinateSystem(extent = {{-100, -100}, {100, 100}}),
      graphics = {
        Rectangle(
          extent = {{-100, 100}, {100, -100}},
          lineColor = {28, 108, 200},
          fillColor = {214, 229, 255},
          fillPattern = FillPattern.Solid),
        Text(
          extent = {{-60, 30}, {60, -10}},
          textString = "SRC",
          textColor = {28, 108, 200},
          textStyle = {TextStyle.Bold},
          fontSize = 8),
        Text(
          extent = {{-90, 90}, {90, -350}},
          textString = "%name",
          textColor = {28, 108, 200},
          fontSize = 8)}),
    version = "");
end PlantStation;
