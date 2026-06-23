within modelica_implementation.Archetypes;

model DHN_THV_3G_L_S_BASE_test
  "Benchmark network DHN_THV_3G_L_S_BASE
   Thermo-Hydraulic Validation — 3rd Generation District Heating — Ring — Small.
   N=19 nodes (1 source, 8 junctions, 10 substations).
   E=19 pipe segments (9 ring DN65 + 10 branch DN25).
   L=1 independent hydraulic loop (single closed ring).
   Simulation: 7 days, 10-min resolution (1008 timesteps).
   Control: CF-VT (constant flow, variable temperature), T_sup=80 degC.
   Ground temperature: 10 degC constant.
  "

  import modelica_implementation.Components.PlantStation;
  import modelica_implementation.Components.DHNPipe;
  import modelica_implementation.Components.DHNJunction;
  import modelica_implementation.Components.BuildingWithIndirectETS;

  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

  inner Modelica.Fluid.System system(
    energyDynamics    = Modelica.Fluid.Types.Dynamics.FixedInitial,
    massDynamics      = Modelica.Fluid.Types.Dynamics.FixedInitial,
    allowFlowReversal = true);

// ---------------------------------------------------------------
  // Global parameters
  // ---------------------------------------------------------------
  parameter Integer nCon = 10
    "Number of ETS connection nodes on the ring (a, b, d, f, h)";

  parameter Modelica.Units.SI.Temperature TDisSupSet = 273.15 + 80
    "District supply temperature setpoint [K]";

  parameter Modelica.Units.SI.Temperature TGround = 273.15 + 10
    "Undisturbed ground temperature [K]";

  parameter Modelica.Units.SI.TemperatureDifference dTDis_nominal = 30
    "Nominal district-side temperature difference at ETS [K]";

  parameter Modelica.Units.SI.Temperature THeaWatSup_nominal = 273.15 + 50
    "Building heating water supply nominal temperature [K]";

  parameter Modelica.Units.SI.Temperature THeaWatRet_nominal = 273.15 + 40
    "Building heating water return nominal temperature [K]";

  parameter Modelica.Units.SI.Pressure pDisSupSet = 1000000
    "Network supply pressure [Pa]";

  parameter String filNam =
    Modelica.Utilities.Files.loadResource(
      "modelica://modelica_implementation/Resources/InputData/demand_profile_base.mos")
    "Path to substation load time-series file";

// ---------------------------------------------------------------
  // Nominal flow rates
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.HeatFlowRate Q_peak_sub = 175000
    "Peak thermal load per substation [W]";

  parameter Modelica.Units.SI.MassFlowRate m_sub = 1.39054
    "Nominal mass flow rate per substation [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_total = nCon * m_sub
    "Total nominal mass flow rate from plant [kg/s]";

  // ---------------------------------------------------------------
  // Central plant
  // ---------------------------------------------------------------
  PlantStation src(
    redeclare package Medium = Medium,
    TDisSup_nominal   = TDisSupSet,
    mDis_flow_nominal = m_total,
    QDis_flow_nominal = 1.2 * nCon * Q_peak_sub,
    p_exp             = pDisSupSet,
    dp_pump_nominal   = 600000,
    dp_pump_set       = 600000,
    dp_heater_nominal = 10000)
    "Central heat plant" annotation(
    Placement(transformation(origin = {-160, -20}, extent = {{-20,-20},{20,20}})));
  
  // ---------------------------------------------------------------
  // ETS substations (10 instances)
  // ---------------------------------------------------------------
  BuildingWithIndirectETS ets[nCon](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam             = filNam,
    each facMul             = 1.0,
    each TDisSup_nominal    = TDisSupSet,
    each THeaWatSup_nominal = THeaWatSup_nominal,
    each THeaWatRet_nominal = THeaWatRet_nominal,
    each dTDis_nominal      = dTDis_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {96, 124}, extent = {{-16,-16},{16,16}})));

  // ---------------------------------------------------------------
  // Derived nominal flow rates
  // ---------------------------------------------------------------
 parameter Modelica.Units.SI.MassFlowRate mCon_flow_nominal[nCon] =
    ets.mDis_flow_nominal * 1.05
    "Nominal mass flow rate at each ETS branch [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate mDis_flow_nominal =
    m_sub * nCon * 1.20
    "Nominal mass flow rate leaving the plant [kg/s]";
  
  // ---------------------------------------------------------------
  // Ring distribution
  // ---------------------------------------------------------------
  Buildings.DHC.Networks.Distribution2PipePlugFlow_v dis(
    redeclare package Medium = Medium,
    nCon                  = nCon,
    mDis_flow_nominal     = mDis_flow_nominal,
    mCon_flow_nominal     = mCon_flow_nominal,
    mEnd_flow_nominal     = m_sub,
    mDisCon_flow_nominal = {mDis_flow_nominal - i*m_sub*1.05 for i in 0:(nCon-1)},
    lDis = {163.9, 163.9, 102.5, 102.5, 249.8, 249.8, 341.3, 341.3, 297.9, 297.9},
    lEnd                  = 142.2,
    v_nominal             = 1.77,
    dIns                  = 0.03195,
    kIns                  = 0.033,
    allowFlowReversal     = true,
    iConDpSen             = nCon,
    roughness             = 4.5e-5,
    thickness             = 0.03195, 
    show_entFlo = true)
    "Ring distribution network" annotation(
    Placement(transformation(origin = {0, -14}, extent = {{-40,-20},{40,20}})));
 
  // ---------------------------------------------------------------
  // Ground temperature
  // ---------------------------------------------------------------
  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroDis[nCon + 1](
    each T = TGround)
    "Ground temperature for supply ring segments" annotation(
    Placement(transformation(origin = {-110, -60}, extent = {{-10,-10},{10,10}})));

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroRet[nCon](
    each T = TGround)
    "Ground temperature for return ring segments" annotation(
    Placement(transformation(origin = {-110, -100}, extent = {{-10,-10},{10,10}})));

  // ---------------------------------------------------------------
  // Branch pipes to substations (10 segments, all DN25)
  // ---------------------------------------------------------------
    DHNPipe pipe_sub[nCon](
    redeclare each package Medium = Medium,
    length = {103.0, 121.9, 150.5, 102.7, 119.9, 165.0, 154.5, 122.0, 158.9, 180.9},
    each d_inner        = 0.0282,
    each dIns           = 0.02815,
    each kIns           = 0.033,
    each roughness      = 4.5e-5,
    m_flow_nominal      = ets.mDis_flow_nominal,
    each TGround        = TGround)
    "Branch pipes sub1..sub10 — DN25" annotation(
    Placement(transformation(origin = {0, 60}, extent = {{-20,-20},{20,20}}, rotation = 90)));

equation

 connect(src.port_bDis, dis.port_aDisSup) annotation(
    Line(points = {{-140, -16}, {-40, -16}, {-40, -14}}, color = {0, 127, 255}));
 connect(dis.port_bDisRet, src.port_aDis) annotation(
    Line(points = {{-40, -26}, {-140, -26}, {-140, -24}}, color = {0, 127, 255}));
 connect(dis.port_bDisSup, dis.port_aDisRet) annotation(
    Line(points = {{40, -14}, {80, -14}, {80, -26}, {40, -26}}, color = {0, 127, 255}));
 connect(dis.ports_bCon, pipe_sub.port_aDisSup) annotation(
    Line(points = {{-24, 6}, {-24, 20}, {-6, 20}, {-6, 40}}, color = {0, 127, 255}, thickness = 0.5));
 connect(pipe_sub.port_bDisSup, ets.port_aSerHea) annotation(
    Line(points = {{-6, 80}, {-6, 121}, {81, 121}}, color = {0, 127, 255}, thickness = 0.5));
 connect(ets.port_bSerHea, pipe_sub.port_aDisRet) annotation(
    Line(points = {{112, 122}, {120, 122}, {120, 100}, {6, 100}, {6, 80}}, color = {0, 127, 255}, thickness = 0.5));
 connect(pipe_sub.port_bDisRet, dis.ports_aCon) annotation(
    Line(points = {{6, 40}, {6, 20}, {24, 20}, {24, 6}}, color = {0, 127, 255}, thickness = 0.5));
 connect(TGroDis.port, dis.heatPortsDis) annotation(
    Line(points = {{-100, -60}, {-60, -60}, {-60, -6}, {16, -6}, {16, -10}}, color = {191, 0, 0}, thickness = 0.5));
 connect(TGroRet.port, dis.heatPortsRet) annotation(
    Line(points = {{-100, -100}, {-14, -100}, {-14, -30}}, color = {191, 0, 0}, thickness = 0.5));

annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    experiment(
      StartTime = 0,
      StopTime  = 604800,
      Tolerance = 1e-06,
      Interval  = 600),
    Diagram(coordinateSystem(extent = {{-200, -150}, {200, 150}})),
    Icon(coordinateSystem(extent = {{-300, -150}, {400, 450}})),
    version = "");
end DHN_THV_3G_L_S_BASE_test;
