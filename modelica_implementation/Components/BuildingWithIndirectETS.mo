within modelica_implementation.Components;
model BuildingWithIndirectETS

  "Indirect energy transfer station with building heating load from time series.
   The district side is hydraulically separated from the building side 
   through a plate heat exchanger with a modulating primary valve.
   The building loop includes its own expansion vessel and circulating pump 
   embedded in the BuildingTimeSeries model.
  "

  replaceable package MediumSer = Buildings.Media.Water
    "District/service side medium";
  replaceable package MediumBui = Buildings.Media.Water
    "Building heating water medium";

  // ---------------------------------------------------------------
  // File input
  // ---------------------------------------------------------------
   parameter String filNam
    "Path to building load time-series file (.mos format)";

   parameter Real facMul = 1
    "Multiplier applied to the building peak load [-]";
 
  // ---------------------------------------------------------------
  // Temperature setpoints and design conditions
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.Temperature TDisSup_nominal = 273.15 + 80
    "Nominal district supply temperature [K]";

  parameter Modelica.Units.SI.Temperature THeaWatSup_nominal = 273.15 + 50
    "Building heating water supply nominal temperature [K]";

  parameter Modelica.Units.SI.Temperature THeaWatRet_nominal = 273.15 + 40
    "Building heating water return nominal temperature [K]";

  parameter Modelica.Units.SI.TemperatureDifference dTBui_nominal =
    THeaWatSup_nominal - THeaWatRet_nominal
    "Building-side nominal temperature difference [K]";

  parameter Modelica.Units.SI.TemperatureDifference dTDis_nominal = 20
    "District-side nominal temperature difference across ETS [K]";
  
  // ---------------------------------------------------------------
  // Fluid properties
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.SpecificHeatCapacity cpWat = 4180
    "Water specific heat capacity (approximate) [J/(kg·K)]";

  // ---------------------------------------------------------------
  // Derived nominal flow rates and loads
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.HeatFlowRate QHea_flow_nominal =
    max(1000, bui.QHea_flow_nominal)
    "Nominal heating load (floor at 1 kW to avoid zero-flow sizing) [W]";

  parameter Modelica.Units.SI.MassFlowRate mBui_flow_nominal =
    QHea_flow_nominal / cpWat / dTBui_nominal
    "Nominal mass flow rate on the building side of the ETS [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate mDis_flow_nominal =
    QHea_flow_nominal / cpWat / dTDis_nominal
    "Nominal mass flow rate on the district side of the ETS [kg/s]";

  // ---------------------------------------------------------------
  // Building load model
  // ---------------------------------------------------------------
  Buildings.DHC.Loads.BaseClasses.BuildingTimeSeries bui(
    redeclare package Medium       = MediumBui,
    final filNam                   = filNam,
    final facMul                   = facMul,
  
    final have_heaWat              = true,
    final have_chiWat              = false,
    final have_hotWat              = false,
  
    final nPorts_aHeaWat           = 1,
    final nPorts_bHeaWat           = 1,
    final nPorts_aChiWat           = 0,
    final nPorts_bChiWat           = 0,
  
    final allowFlowReversal        = false,
  
    final T_aHeaWat_nominal        = THeaWatSup_nominal,
    final T_bHeaWat_nominal        = THeaWatRet_nominal,
    
    final T_aLoaHea_nominal        = 293.15,
    final mLoaHea_flow_nominal     = 0.5,
    
    final T_aHeaWat_nominal_ref    = 323.15,
    final T_aLoaHea_nominal_ref    = 293.15,
    final mLoaHea_flow_nominal_ref = 0.5,
    final QHea_flow_nominal_ref    = 4500,
    
    disFloHea(
      energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial,
      tau = 120))
    "Heating-only building load from time series" annotation(
    Placement(transformation(origin = {0, 60}, extent = {{-30, -30}, {30, 30}})));
      
  // ---------------------------------------------------------------
  // Energy Transfer Station (ETS)
  // ---------------------------------------------------------------
  Buildings.DHC.ETS.Heating.Indirect ets(
    redeclare package MediumSer = MediumSer,
    redeclare package MediumBui = MediumBui,
    mDis_flow_nominal           = mDis_flow_nominal,
    mBui_flow_nominal           = mBui_flow_nominal,
    dp1_nominal                 = 10000,
    dp2_nominal                 = 10000,
    dpConVal_nominal            = 6000,
    T_a1_nominal                = TDisSup_nominal,
    T_a2_nominal                = THeaWatRet_nominal,
    use_Q_flow_nominal          = true,
    Q_flow_nominal              = QHea_flow_nominal,
    eta                         = 0.8,
    yMin                        = 0.03)
    "Indirect ETS with primary valve and heat exchanger" annotation(
    Placement(transformation(origin = {0, -30}, extent = {{-30, -30}, {30, 30}})));

  Modelica.Blocks.Sources.Constant TBuiSupSet(
     k = THeaWatSup_nominal)
    "Building heating water supply setpoint" annotation(
    Placement(transformation(origin = {-80, 40}, extent = {{-10, -10}, {10, 10}})));
   
  // ---------------------------------------------------------------
  // Instrumentation sensors — district side
  // ---------------------------------------------------------------
  Buildings.Fluid.Sensors.TemperatureTwoPort senT_disSup(
    redeclare package Medium = MediumSer,
    m_flow_nominal    = mDis_flow_nominal,
    allowFlowReversal = false,
    tau               = 0)
    "District supply temperature at ETS inlet [K]" annotation(
    Placement(transformation(origin = {-65, -54}, extent = {{-10, -10}, {10, 10}})));

  Buildings.Fluid.Sensors.TemperatureTwoPort senT_disRet(
    redeclare package Medium = MediumSer,
    m_flow_nominal    = mDis_flow_nominal,
    allowFlowReversal = false,
    tau               = 0)
    "District return temperature at ETS outlet [K]" annotation(
    Placement(transformation(origin = {65, -54}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // External fluid ports (district side)
  // ---------------------------------------------------------------
  Modelica.Fluid.Interfaces.FluidPort_a port_aSerHea(
    redeclare package Medium = MediumSer)
    "District supply to ETS" annotation(
    Placement(transformation(origin = {-100, -54}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {-94, -18}, extent = {{-10, -10}, {10, 10}})));
  
  Modelica.Fluid.Interfaces.FluidPort_b port_bSerHea(
    redeclare package Medium = MediumSer)
    "District return from ETS" annotation(
    Placement(transformation(origin = {100, -54}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {100, -16}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // Output signals
  // ---------------------------------------------------------------
  Modelica.Blocks.Interfaces.RealOutput QHea_flow "Building heating load" annotation(
    Placement(transformation(origin = {130, 86}, extent = {{-10, -10}, {10, 10}}), iconTransformation(origin = {106, 24}, extent = {{-10, -10}, {10, 10}})));
  
  // ---------------------------------------------------------------
  // Output signals
  // ---------------------------------------------------------------
  Buildings.Fluid.Sources.Boundary_pT expBui(
  redeclare package Medium = MediumBui,
  p = 300000,
  T = THeaWatSup_nominal,
  nPorts = 1)
  "Pressure reference / expansion vessel for the isolated building loop" annotation(
    Placement(transformation(origin = {-88, -4}, extent = {{-10, -10}, {10, 10}})));

equation
  connect(ets.ports_bHeaWat[1], bui.ports_aHeaWat[1]) annotation(
    Line(points = {{30, -4}, {40, -4}, {40, 12}, {-40, 12}, {-40, 54}, {-30, 54}}, color = {0, 127, 255}));
  connect(bui.ports_bHeaWat[1], ets.ports_aHeaWat[1]) annotation(
    Line(points = {{30, 54}, {40, 54}, {40, 20}, {-48, 20}, {-48, -4}, {-30, -4}}, color = {0, 127, 255}));
  connect(TBuiSupSet.y, ets.TBuiSupSet) annotation(
    Line(points = {{-69, 40}, {-60, 40}, {-60, -30}, {-32, -30}}, color = {0, 0, 127}));
  connect(bui.QHea_flow, QHea_flow) annotation(
    Line(points = {{32, 86}, {130, 86}}, color = {0, 0, 127}));
  connect(expBui.ports[1], ets.ports_aHeaWat[1]) annotation(
    Line(points = {{-78, -4}, {-30, -4}}, color = {0, 127, 255}));
  connect(port_aSerHea, senT_disSup.port_a) annotation(
    Line(points = {{-100, -54}, {-74, -54}}));
  connect(senT_disSup.port_b, ets.port_aSerHea) annotation(
    Line(points = {{-54, -54}, {-30, -54}}, color = {0, 127, 255}));
  connect(ets.port_bSerHea, senT_disRet.port_a) annotation(
    Line(points = {{30, -54}, {56, -54}}, color = {0, 127, 255}));
  connect(senT_disRet.port_b, port_bSerHea) annotation(
    Line(points = {{76, -54}, {100, -54}}, color = {0, 127, 255}));

annotation(
  uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
  Diagram(coordinateSystem(extent = {{-100, -100}, {100, 100}})),
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
          textString = "ETS",
          textColor = {28, 108, 200},
          textStyle = {TextStyle.Bold},
          fontSize = 8),
        Text(
          extent = {{-90, 90}, {90, -350}},
          textString = "%name",
          textColor = {28, 108, 200},
          fontSize = 8)}),
  version = "");
end BuildingWithIndirectETS;
