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
  parameter Integer nCon = 5
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

  parameter Modelica.Units.SI.MassFlowRate m_total = 10 * m_sub
    "Total nominal mass flow rate from plant [kg/s]";

  // ---------------------------------------------------------------
  // Central plant
  // ---------------------------------------------------------------
  PlantStation src(
    redeclare package Medium = Medium,
    TDisSup_nominal   = TDisSupSet,
    mDis_flow_nominal = m_total,
    QDis_flow_nominal = 1.2 * 10 * Q_peak_sub,
    p_exp             = pDisSupSet,
    dp_pump_nominal   = 600000,
    dp_pump_set       = 600000,
    dp_heater_nominal = 10000)
    "Central heat plant" annotation(
    Placement(transformation(origin = {-220, -20}, extent = {{-20,-20},{20,20}})));
  
  // ---------------------------------------------------------------
  // ETS substations (10 instances)
  // ---------------------------------------------------------------
  BuildingWithIndirectETS ets[10](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam             = filNam,
    each facMul             = 1.0,
    each TDisSup_nominal    = TDisSupSet,
    each THeaWatSup_nominal = THeaWatSup_nominal,
    each THeaWatRet_nominal = THeaWatRet_nominal,
    each dTDis_nominal      = dTDis_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {296, 182}, extent = {{-16,-16},{16,16}})));

  // ---------------------------------------------------------------
  // Ring distribution — Distribution2PipePlugFlow_v
  // nCon=5 nodes: a, b, d, f, h
  // mDis_flow_nominal = m_total
  // mEnd_flow_nominal = m_total
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.MassFlowRate mCon_flow_nominal[nCon] = {
    ets[1].mDis_flow_nominal + ets[2].mDis_flow_nominal,
    ets[3].mDis_flow_nominal + ets[4].mDis_flow_nominal,
    ets[5].mDis_flow_nominal + ets[6].mDis_flow_nominal,
    ets[7].mDis_flow_nominal + ets[8].mDis_flow_nominal,
    ets[9].mDis_flow_nominal + ets[10].mDis_flow_nominal}
    "Nominal mass flow rate at each connection node (2 ETS in parallel) [kg/s]";
  
  parameter Modelica.Units.SI.MassFlowRate mEnd_flow_nominal =
    ets[9].mDis_flow_nominal + ets[10].mDis_flow_nominal
    "Nominal mass flow rate in ring closure segment [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate mDis_flow_nominal =
    sum(mCon_flow_nominal) + mEnd_flow_nominal
    "Nominal mass flow rate leaving the plant [kg/s]";
    
  Buildings.DHC.Networks.Distribution2PipePlugFlow_v dis(
    redeclare package Medium = Medium,
    final nCon            = nCon,
    mDis_flow_nominal     = mDis_flow_nominal, 
    mCon_flow_nominal     = mCon_flow_nominal,
    mEnd_flow_nominal     = mEnd_flow_nominal,
    lDis                  = {163.9, 266.4, 516.2, 857.5, 1155.4},
    lEnd                  = 142.2,
    v_nominal             = 1.77,
    dIns                  = 0.03195,
    kIns                  = 0.033,
    allowFlowReversal     = true,
    iConDpSen             = nCon, 
    roughness             = 4.50e-5, 
    thickness             = 0.03195)
    "Ring distribution network" annotation(
    Placement(transformation(origin = {0, -14}, extent = {{-40,-20},{40,20}})));
 
  // ---------------------------------------------------------------
  // Ground temperature
  // ---------------------------------------------------------------
  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroDis[nCon + 1](
    each T = TGround)
    "Ground temperature for supply ring segments" annotation(
    Placement(transformation(origin = {-160, -60}, extent = {{-10,-10},{10,10}})));

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroRet[nCon](
    each T = TGround)
    "Ground temperature for return ring segments" annotation(
    Placement(transformation(origin = {-160, -100}, extent = {{-10,-10},{10,10}})));

  // ---------------------------------------------------------------
  // Branch pipes — 10 segments DN25
  // ---------------------------------------------------------------
 

equation


annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    experiment(
      StartTime = 0,
      StopTime  = 604800,
      Tolerance = 1e-06,
      Interval  = 600),
    Diagram(coordinateSystem(extent = {{-300, -150}, {400, 450}})),
    Icon(coordinateSystem(extent = {{-300, -150}, {400, 450}})),
    version = "");
end DHN_THV_3G_L_S_BASE_test;
