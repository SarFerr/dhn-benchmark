within modelica_implementation.Components;
model DHNPipe
  "Two-pipe district heating segment (supply + return) with plug-flow thermal
   transport and linear heat losses to the ground.
   The supply and return pipes share the same geometric and thermal parameters.
  "

  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

  // ---------------------------------------------------------------
  // Fluid properties
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.Density rho_nominal = 971.8
    "Fluid density at nominal operating conditions [kg/m3]";

  parameter Modelica.Units.SI.SpecificHeatCapacity cp_nominal = 4195.0
    "Fluid specific heat capacity at nominal operating conditions [J/(kg·K)]";

  // ---------------------------------------------------------------
  // Geometric parameters
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.Length length = 100
    "Pipe segment length [m]";

  parameter Modelica.Units.SI.Diameter d_inner = 0.0545
    "Inner diameter of the carrier pipe [m]";

  parameter Modelica.Units.SI.Length dIns = 0.032
    "Insulation thickness [m]";

  parameter Modelica.Units.SI.ThermalConductivity kIns = 0.033
    "Insulation thermal conductivity (PUR foam) [W/(m·K)]";

  parameter Modelica.Units.SI.Length roughness = 4.5e-5
    "Pipe wall roughness [m]";

  // ---------------------------------------------------------------
  // Thermal boundary condition
  // ---------------------------------------------------------------
    parameter Modelica.Units.SI.Temperature T_start = 273.15 + 80
    "Initial temperature [K]";
  
  parameter Modelica.Units.SI.Temperature TGround = 273.15 + 10
    "Undisturbed ground temperature [K]";

  // ---------------------------------------------------------------
  // Hydraulic parameters
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.MassFlowRate m_flow_nominal = 0.5
    "Nominal mass flow rate [kg/s]";

  parameter Boolean allowFlowReversal = false
    "= true to allow flow reversal in the pipe";

  // ---------------------------------------------------------------
  // Supply pipe
  // ---------------------------------------------------------------
  Buildings.Fluid.FixedResistances.PlugFlowPipe pipSup(
    redeclare package Medium = Medium,
    final length            = length,
    final dIns              = dIns,
    final kIns              = kIns,
    final dh                = d_inner,
    final roughness         = roughness,
    final m_flow_nominal    = m_flow_nominal,
    final allowFlowReversal = allowFlowReversal, 
    T_start_in = T_start, 
    T_start_out = T_start)
    "Supply pipe segment with plug-flow thermal transport" annotation(
    Placement(transformation(origin = {0, 40}, extent = {{-10, -10}, {10, 10}})));

  // ---------------------------------------------------------------
  // Return pipe
  // ---------------------------------------------------------------
  Buildings.Fluid.FixedResistances.PlugFlowPipe pipRet(
    redeclare package Medium = Medium,
    final length            = length,
    final dIns              = dIns,
    final kIns              = kIns,
    final dh                = d_inner,
    final roughness         = roughness,
    final m_flow_nominal    = m_flow_nominal,
    final allowFlowReversal = allowFlowReversal, 
    T_start_in = T_start, 
    T_start_out = T_start)
    "Return pipe segment with plug-flow thermal transport" annotation(
    Placement(transformation(origin = {0, -40}, extent = {{10, 10}, {-10, -10}})));

  // ---------------------------------------------------------------
  // Ground temperature boundary conditions
  // ---------------------------------------------------------------
  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroSup(
    T = TGround)
    "Ground temperature source for supply pipe" annotation(
    Placement(transformation(origin = {-90, 80}, extent = {{-10, 10}, {10, -10}})));

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroRet(
    T = TGround)
    "Ground temperature source for return pipe" annotation(
    Placement(transformation(origin = {-90, -80}, extent = {{-10, 10}, {10, -10}})));

  // ---------------------------------------------------------------
  // Instrumentation sensors
  // ---------------------------------------------------------------
  Buildings.Fluid.Sensors.TemperatureTwoPort senT_supIn(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Supply temperature at pipe inlet [K]" annotation(
    Placement(transformation(origin = {-50, 40}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.TemperatureTwoPort senT_supOut(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Supply temperature at pipe outlet [K]" annotation(
    Placement(transformation(origin = {70, 40}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.TemperatureTwoPort senT_retIn(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Return temperature at pipe inlet [K]" annotation(
    Placement(transformation(origin = {50, -40}, extent = {{10, -10}, {-10, 10}})));

  Buildings.Fluid.Sensors.TemperatureTwoPort senT_retOut(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Return temperature at pipe outlet [K]" annotation(
    Placement(transformation(origin = {-70, -40}, extent = {{10, -10}, {-10, 10}})));

  Buildings.Fluid.Sensors.MassFlowRate senM_sup(
    redeclare package Medium = Medium,
    allowFlowReversal = allowFlowReversal)
    "Mass flow rate in supply pipe [kg/s]" annotation(
    Placement(transformation(origin = {-90, 40}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.MassFlowRate senM_ret(
    redeclare package Medium = Medium,
    allowFlowReversal = allowFlowReversal)
    "Mass flow rate in return pipe [kg/s]" annotation(
    Placement(transformation(origin = {90, -40}, extent = {{10, -10}, {-10, 10}})));

// ---------------------------------------------------------------
  // Derived output variables
  // ---------------------------------------------------------------
  Modelica.Units.SI.Velocity v_sup
    "Mean flow velocity in supply pipe [m/s]";

  Modelica.Units.SI.Velocity v_ret
    "Mean flow velocity in return pipe [m/s]";

  Modelica.Units.SI.HeatFlowRate Q_loss_sup
    "Heat loss from supply pipe to ground [W]";

  Modelica.Units.SI.HeatFlowRate Q_loss_ret
    "Heat loss from return pipe to ground [W]";

  // ---------------------------------------------------------------
  // External fluid ports — supply side
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_a port_aDisSup(
    redeclare package Medium = Medium)
    "Supply pipe inlet (from upstream junction or plant)" annotation(
    Placement(transformation(origin = {-120, 40}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {-100, 30}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_b port_bDisSup(
    redeclare package Medium = Medium)
    "Supply pipe outlet (to downstream junction or ETS)" annotation(
    Placement(transformation(origin = {120, 40}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {100, 30}, extent = {{-10, -10}, {10, 10}})));

  // ---------------------------------------------------------------
  // External fluid ports — return side
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_a port_aDisRet(
    redeclare package Medium = Medium)
    "Return pipe inlet (from downstream junction or ETS)" annotation(
    Placement(transformation(origin = {120, -40}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {100, -30}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_b port_bDisRet(
    redeclare package Medium = Medium)
    "Return pipe outlet (to upstream junction or plant)" annotation(
    Placement(transformation(origin = {-120, -40}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {-100, -30}, extent = {{-10, -10}, {10, 10}})));

equation
// ---------------------------------------------------------------
// Supply pipe connections
// ---------------------------------------------------------------
  connect(port_aDisSup, senM_sup.port_a) annotation(
    Line(points = {{-120, 40}, {-100, 40}}));
  connect(senM_sup.port_b, senT_supIn.port_a) annotation(
    Line(points = {{-80, 40}, {-60, 40}}, color = {0, 127, 255}));
  connect(senT_supIn.port_b, pipSup.port_a) annotation(
    Line(points = {{-40, 40}, {-10, 40}}, color = {0, 127, 255}));
  connect(pipSup.port_b, senT_supOut.port_a) annotation(
    Line(points = {{10, 40}, {60, 40}}, color = {0, 127, 255}));
  connect(senT_supOut.port_b, port_bDisSup) annotation(
    Line(points = {{80, 40}, {120, 40}}, color = {0, 127, 255}));
  connect(TGroSup.port, pipSup.heatPort) annotation(
    Line(points = {{-80, 80}, {0, 80}, {0, 50}}, color = {191, 0, 0}));
// ---------------------------------------------------------------
// Return pipe connections
// ---------------------------------------------------------------
  connect(port_aDisRet, senM_ret.port_a) annotation(
    Line(points = {{120, -40}, {100, -40}}));
  connect(senM_ret.port_b, senT_retIn.port_a) annotation(
    Line(points = {{80, -40}, {60, -40}}, color = {0, 127, 255}));
  connect(senT_retIn.port_b, pipRet.port_a) annotation(
    Line(points = {{40, -40}, {10, -40}}, color = {0, 127, 255}));
  connect(pipRet.port_b, senT_retOut.port_a) annotation(
    Line(points = {{-10, -40}, {-60, -40}}, color = {0, 127, 255}));
  connect(senT_retOut.port_b, port_bDisRet) annotation(
    Line(points = {{-80, -40}, {-120, -40}}, color = {0, 127, 255}));
  connect(TGroRet.port, pipRet.heatPort) annotation(
    Line(points = {{-80, -80}, {0, -80}, {0, -50}}, color = {191, 0, 0}));
// ---------------------------------------------------------------
// Derived variable equations
// ---------------------------------------------------------------
  v_sup = abs(senM_sup.m_flow) /
          (rho_nominal * Modelica.Constants.pi * (d_inner / 2)^2);

  v_ret = abs(senM_ret.m_flow) /
          (rho_nominal * Modelica.Constants.pi * (d_inner / 2)^2);

  Q_loss_sup = pipSup.heatPort.Q_flow;

  Q_loss_ret = pipRet.heatPort.Q_flow;

  annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    Icon(
      coordinateSystem(
        extent = {{-100, -100}, {100, 100}},
        preserveAspectRatio = true),
      graphics = {
        Rectangle(
          extent = {{-100, 60}, {100, -60}},
          lineColor = {28, 108, 200},
          fillColor = {214, 229, 255},
          fillPattern = FillPattern.Solid),
        Text(
          extent = {{-90, 90}, {90, -280}},
          textString = "%name",
          textColor = {28, 108, 200},
          fontSize = 8),
        Text(
          extent = {{-60, 20}, {60, -20}},
          textString = "PIPE",
          textColor = {28, 108, 200},
          textStyle = {TextStyle.Bold},
          fontSize = 8)}),
    Diagram(coordinateSystem(extent = {{-150, -100}, {150, 100}})),
    version = "");
end DHNPipe;
