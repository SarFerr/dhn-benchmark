within modelica_implementation.Components;
model DHNJunction
  "Two-pipe district heating junction (T-piece) for radial tree networks.
   Each instance represents one T-junction on both supply and return sides.
   On the supply side: one inlet splits into two outlets.
   On the return side: two inlets merge into one outlet.
   The junction is ideal (no pressure drop, instantaneous mixing).
  "

  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

// ---------------------------------------------------------------
  // Hydraulic parameters
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.MassFlowRate m_flow_nominal = 0.5
    "Nominal mass flow rate at the main inlet [kg/s]";

  parameter Boolean allowFlowReversal = false
    "= true to allow flow reversal";

// ---------------------------------------------------------------
  // Supply junction (1 inlet → 2 outlets)
  // ---------------------------------------------------------------
  Buildings.Fluid.FixedResistances.Junction junSup(
    redeclare package Medium = Medium,
    m_flow_nominal      = {m_flow_nominal, -m_flow_nominal/2, -m_flow_nominal/2},
    dp_nominal          = {0, 0, 0},
    portFlowDirection_1 = Modelica.Fluid.Types.PortFlowDirection.Entering,
    portFlowDirection_2 = Modelica.Fluid.Types.PortFlowDirection.Leaving,
    portFlowDirection_3 = Modelica.Fluid.Types.PortFlowDirection.Leaving)
    "Supply side T-junction: flow splits from port_1 to port_2 and port_3" annotation(
    Placement(transformation(origin = {40, 20}, extent = {{-10, -10}, {10, 10}})));

// ---------------------------------------------------------------
  // Return junction (2 inlets → 1 outlet)
  // ---------------------------------------------------------------
  Buildings.Fluid.FixedResistances.Junction junRet(
    redeclare package Medium = Medium,
    m_flow_nominal      = {m_flow_nominal, -m_flow_nominal/2, -m_flow_nominal/2},
    dp_nominal          = {0, 0, 0},
    portFlowDirection_1 = Modelica.Fluid.Types.PortFlowDirection.Leaving,
    portFlowDirection_2 = Modelica.Fluid.Types.PortFlowDirection.Entering,
    portFlowDirection_3 = Modelica.Fluid.Types.PortFlowDirection.Entering)
    "Return side T-junction: flow merges from port_2 and port_3 into port_1" annotation(
    Placement(transformation(origin = {0, -20}, extent = {{-10, -10}, {10, 10}})));

// ---------------------------------------------------------------
  // Instrumentation sensors
  // ---------------------------------------------------------------
  Buildings.Fluid.Sensors.TemperatureTwoPort senT_supIn(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Supply temperature at junction inlet [K]" annotation(
    Placement(transformation(origin = {-40, 20}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.TemperatureTwoPort senT_retOut(
    redeclare package Medium = Medium,
    m_flow_nominal    = m_flow_nominal,
    allowFlowReversal = allowFlowReversal,
    tau               = 0)
    "Return temperature at junction outlet (mixed return) [K]" annotation(
    Placement(transformation(origin = {-50, -20}, extent = {{10, -10}, {-10, 10}})));

  Buildings.Fluid.Sensors.MassFlowRate senM_supIn(
    redeclare package Medium = Medium,
    allowFlowReversal = allowFlowReversal)
    "Total mass flow rate entering the junction on supply side [kg/s]" annotation(
    Placement(transformation(origin = {-80, 20}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.MassFlowRate senM_supOut1(
    redeclare package Medium = Medium,
    allowFlowReversal = allowFlowReversal)
    "Mass flow rate leaving junction toward first downstream branch [kg/s]" annotation(
    Placement(transformation(origin = {80, 20}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.MassFlowRate senM_supOut2(
    redeclare package Medium = Medium,
    allowFlowReversal = allowFlowReversal)
    "Mass flow rate leaving junction toward second downstream branch [kg/s]" annotation(
    Placement(transformation(origin = {40, -40}, extent = {{-10, 10}, {10, -10}}, rotation = -90)));

// ---------------------------------------------------------------
  // External fluid ports — supply side
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_a port_aSupIn(
    redeclare package Medium = Medium)
    "Supply inlet (from upstream trunk pipe)" annotation(
    Placement(transformation(origin = {-120, 20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {-30, -60}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_b port_bSupOut1(
    redeclare package Medium = Medium)
    "Supply outlet 1 (to first downstream branch)" annotation(
    Placement(transformation(origin = {120, 20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {60, 30}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_b port_bSupOut2(
    redeclare package Medium = Medium)
    "Supply outlet 2 (to second downstream branch)" annotation(
    Placement(transformation(origin = {40, -82}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {-60, -30}, extent = {{-10, -10}, {10, 10}})));

// ---------------------------------------------------------------
  // External fluid ports — return side
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_b port_bRetOut(
    redeclare package Medium = Medium)
    "Return outlet (to upstream trunk pipe)" annotation(
    Placement(transformation(origin = {-120, -20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {30, -60}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_a port_aRetIn1(
    redeclare package Medium = Medium)
    "Return inlet 1 (from first downstream branch)" annotation(
    Placement(transformation(origin = {120, -20}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {60, -30}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Fluid.Interfaces.FluidPort_a port_aRetIn2(
    redeclare package Medium = Medium)
    "Return inlet 2 (from second downstream branch)" annotation(
    Placement(transformation(origin = {0, -80}, extent = {{-10, -10}, {10, 10}}),
    iconTransformation(origin = {-60, 30}, extent = {{-10, -10}, {10, 10}})));

equation
// ---------------------------------------------------------------
// Supply side connections
// ---------------------------------------------------------------
  connect(port_aSupIn, senM_supIn.port_a) annotation(
    Line(points = {{-120, 20}, {-90, 20}}));
  connect(senM_supIn.port_b, senT_supIn.port_a) annotation(
    Line(points = {{-70, 20}, {-50, 20}}, color = {0, 127, 255}));
  connect(senT_supIn.port_b, junSup.port_1) annotation(
    Line(points = {{-30, 20}, {30, 20}}, color = {0, 127, 255}));
  connect(junSup.port_2, senM_supOut1.port_a) annotation(
    Line(points = {{50, 20}, {70, 20}}, color = {0, 127, 255}));
  connect(senM_supOut1.port_b, port_bSupOut1) annotation(
    Line(points = {{90, 20}, {120, 20}}, color = {0, 127, 255}));
  connect(junSup.port_3, senM_supOut2.port_a) annotation(
    Line(points = {{40, 10}, {40, -30}}, color = {0, 127, 255}));
  connect(senM_supOut2.port_b, port_bSupOut2) annotation(
    Line(points = {{40, -50}, {40, -82}}, color = {0, 127, 255}));
// ---------------------------------------------------------------
// Return side connections
// ---------------------------------------------------------------
  connect(port_aRetIn1, junRet.port_2) annotation(
    Line(points = {{120, -20}, {10, -20}}));
  connect(junRet.port_1, senT_retOut.port_a) annotation(
    Line(points = {{-10, -20}, {-40, -20}}, color = {0, 127, 255}));
  connect(senT_retOut.port_b, port_bRetOut) annotation(
    Line(points = {{-60, -20}, {-120, -20}}, color = {0, 127, 255}));
  connect(port_aRetIn2, junRet.port_3) annotation(
    Line(points = {{0, -80}, {0, -30}}));

  annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    Icon(
      coordinateSystem(
        extent = {{-100, -100}, {100, 100}},
        preserveAspectRatio = true),
      graphics = {
        Rectangle(
          extent = {{-60, 60}, {60, -60}},
          lineColor = {100, 100, 100},
          fillColor = {235, 235, 235},
          fillPattern = FillPattern.Solid),
        Text(
          extent = {{-90, 90}, {90, -280}},
          textString = "%name",
          textColor = {100, 100, 100},
          fontSize = 8),
        Text(
          extent = {{-40, 20}, {40, -20}},
          textString = "JUN",
          textColor = {100, 100, 100},
          textStyle = {TextStyle.Bold},
          fontSize = 8)}),
    Diagram(coordinateSystem(extent = {{-150, -150}, {150, 150}})),
    version = "");
end DHNJunction;
