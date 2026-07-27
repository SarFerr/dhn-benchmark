within modelica_implementation.Archetypes;

model DHN_THV_3G_L_S_BASE_1
  "Benchmark network DHN_THV_3G_L_S_BASE
   Thermo-Hydraulic Validation — 3rd Generation District Heating — Ring — Small.
   N=19 nodes (1 source, 8 junctions, 10 substations).
   E=19 pipe segments (9 ring DN25 + 10 branch DN25).
   L=1 independent hydraulic loop (single closed ring).
   Simulation: 7 days, 10-min resolution (1008 timesteps).
   Control: CF-VT (constant flow, variable temperature), T_sup=80 degC.
   Ground temperature: 10 degC constant.
  "

  import modelica_implementation.Components.PlantStation;
  import modelica_implementation.Components.DHNJunction;
  import modelica_implementation.Components.DHNPipe;
  import modelica_implementation.Components.BuildingWithIndirectETS;

  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

  inner Modelica.Fluid.System system(
    energyDynamics    = Modelica.Fluid.Types.Dynamics.SteadyState,
    massDynamics      = Modelica.Fluid.Types.Dynamics.FixedInitial);

// ---------------------------------------------------------------
  // Global network parameters
  // ---------------------------------------------------------------
  parameter Integer nSub = 10
    "Number of substations";

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
    "Network supply pressure at plant (expansion vessel) [Pa]";

  parameter String filNam =
    Modelica.Utilities.Files.loadResource(
      "modelica://modelica_implementation/Resources/InputData/demand_profile_base.mos")
    "Path to substation load time-series file";

// ---------------------------------------------------------------
  // Nominal flow rates (bottom-up sizing from substations)
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.HeatFlowRate Q_peak_sub = 175000
    "Peak thermal load per substation [W]";

  parameter Modelica.Units.SI.HeatFlowRate Q_peak_total = nSub * Q_peak_sub
    "Total peak thermal load [W]";

  parameter Modelica.Units.SI.MassFlowRate m_sub = 1.39054
    "Nominal mass flow rate per substation [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_ring = nSub * m_sub / 2
    "Nominal mass flow rate in ring segments (half total) [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_total = nSub * m_sub
    "Total nominal mass flow rate from plant [kg/s]";

// ---------------------------------------------------------------
  // Central plant
  // ---------------------------------------------------------------
  PlantStation src(
    redeclare package Medium = Medium,
    TDisSup_nominal   = TDisSupSet,
    mDis_flow_nominal = m_total,
    QDis_flow_nominal = 1.2 * Q_peak_total,
    p_exp             = pDisSupSet,
    dp_pump_nominal   = 600000,
    dp_pump_set       = 600000,
    dp_heater_nominal = 10000)
    "Central heat plant" annotation(
    Placement(transformation(origin = {-200, 240}, extent = {{-20, -20}, {20, 20}})));

// ---------------------------------------------------------------
  // Source junctions — src connects to ring pipe src_a (outlet)
  // and ring pipe h_src (inlet), so we need a split/merge junction
  // ---------------------------------------------------------------
  DHNJunction jun_src(
    redeclare package Medium = Medium,
    m_flow_nominal = m_total)
    "Source junction: connects plant to ring pipes src_a and h_src" annotation(
    Placement(transformation(origin = {-120, 240}, extent = {{-20, -20}, {20, 20}})));

// ---------------------------------------------------------------
  // Ring pipes (9 segments, all DN65)
  // ---------------------------------------------------------------
  DHNPipe pipe_src_a(
    redeclare package Medium = Medium,
    length         = 163.9,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: src to a — DN65, 163.9 m" annotation(
    Placement(transformation(origin = {-120, 140}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_a_b(
    redeclare package Medium = Medium,
    length         = 102.5,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: a to b — DN65, 102.5 m" annotation(
    Placement(transformation(origin = {-120, -14}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_b_c(
    redeclare package Medium = Medium,
    length         = 127.5,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: b to c — DN65, 127.5 m" annotation(
    Placement(transformation(origin = {-120, -160}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_c_d(
    redeclare package Medium = Medium,
    length         = 122.3,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: c to d — DN65, 122.3 m" annotation(
    Placement(transformation(origin = {20, -210}, extent = {{-20, -20}, {20, 20}})));

  DHNPipe pipe_d_e(
    redeclare package Medium = Medium,
    length         = 173.6,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: d to e — DN65, 173.6 m" annotation(
    Placement(transformation(origin = {220, -210}, extent = {{-20, -20}, {20, 20}})));

  DHNPipe pipe_e_f(
    redeclare package Medium = Medium,
    length         = 167.7,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: e to f — DN65, 167.7 m" annotation(
    Placement(transformation(origin = {360, -76}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

  DHNPipe pipe_f_g(
    redeclare package Medium = Medium,
    length         = 189.2,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: f to g — DN65, 189.2 m" annotation(
    Placement(transformation(origin = {360, 120}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

  DHNPipe pipe_g_h(
    redeclare package Medium = Medium,
    length         = 108.7,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: g to h — DN65, 108.7 m" annotation(
    Placement(transformation(origin = {220, 240}, extent = {{20, 20}, {-20, -20}}, rotation = -0)));

  DHNPipe pipe_h_src(
    redeclare package Medium = Medium,
    length         = 142.2,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_ring,
    TGround        = TGround)
    "Ring: h to src — DN65, 142.2 m" annotation(
    Placement(transformation(origin = {20, 240}, extent = {{20, 20}, {-20, -20}}, rotation = -0)));

// ---------------------------------------------------------------
  // Branch pipes to substations (10 segments, all DN25)
  // ---------------------------------------------------------------
  DHNPipe pipe_a_sub1(
    redeclare package Medium = Medium,
    length         = 103.0,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch a to sub1 — DN25, 103.0 m" annotation(
    Placement(transformation(origin = {-200, 80}, extent = {{20, 20}, {-20, -20}})));

  DHNPipe pipe_a_sub2(
    redeclare package Medium = Medium,
    length         = 121.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch a to sub2 — DN25, 121.9 m" annotation(
    Placement(transformation(origin = {-40, 40}, extent = {{-20, 20}, {20, -20}}, rotation = -0)));

  DHNPipe pipe_b_sub3(
    redeclare package Medium = Medium,
    length         = 150.5,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch b to sub3 — DN25, 150.5 m" annotation(
    Placement(transformation(origin = {-200, -70}, extent = {{20, 20}, {-20, -20}}, rotation = -0)));

  DHNPipe pipe_b_sub4(
    redeclare package Medium = Medium,
    length         = 102.7,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch b to sub4 — DN25, 102.7 m" annotation(
    Placement(transformation(origin = {-40, -112}, extent = {{-20, 20}, {20, -20}}, rotation = -0)));

  DHNPipe pipe_d_sub5(
    redeclare package Medium = Medium,
    length         = 119.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch d to sub5 — DN25, 119.9 m" annotation(
    Placement(transformation(origin = {100, -164}, extent = {{20, -20}, {-20, 20}}, rotation = -90)));

  DHNPipe pipe_d_sub6(
    redeclare package Medium = Medium,
    length         = 165.0,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch d to sub6 — DN25, 165.0 m" annotation(
    Placement(transformation(origin = {152, -270}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_f_sub7(
    redeclare package Medium = Medium,
    length         = 154.5,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch f to sub7 — DN25, 154.5 m" annotation(
    Placement(transformation(origin = {280, -6}, extent = {{20, -20}, {-20, 20}})));

  DHNPipe pipe_f_sub8(
    redeclare package Medium = Medium,
    length         = 122.0,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch f to sub8 — DN25, 122.0 m" annotation(
    Placement(transformation(origin = {440, 52}, extent = {{-20, -20}, {20, 20}})));

  DHNPipe pipe_h_sub9(
    redeclare package Medium = Medium,
    length         = 158.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch h to sub9 — DN25, 158.9 m" annotation(
    Placement(transformation(origin = {100, 300}, extent = {{20, -20}, {-20, 20}}, rotation = -90)));

  DHNPipe pipe_h_sub10(
    redeclare package Medium = Medium,
    length         = 180.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch h to sub10 — DN25, 180.9 m" annotation(
    Placement(transformation(origin = {152, 180}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // Junctions — node a (degree 4: ring_in, ring_out, sub1, sub2)
  // ---------------------------------------------------------------
  DHNJunction jun_a1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring)
    "Junction a1: splits toward sub1 and remainder" annotation(
    Placement(transformation(origin = {-120, 80}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNJunction jun_a2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction a2: splits toward sub2 and ring_a_b" annotation(
    Placement(transformation(origin = {-120, 40}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // Junctions — node b (degree 4: ring_in, ring_out, sub3, sub4)
  // ---------------------------------------------------------------
  DHNJunction jun_b1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring)
    "Junction b1: splits toward sub3 and remainder" annotation(
    Placement(transformation(origin = {-120, -72}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNJunction jun_b2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction b2: splits toward sub4 and ring_b_c" annotation(
    Placement(transformation(origin = {-120, -112}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // Junctions — node d (degree 4: ring_in, ring_out, sub5, sub6)
  // ---------------------------------------------------------------
  DHNJunction jun_d1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring)
    "Junction d1: splits toward sub5 and remainder" annotation(
    Placement(transformation(origin = {100, -210}, extent = {{-20, -20}, {20, 20}})));

  DHNJunction jun_d2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction d2: splits toward sub6 and ring_d_e" annotation(
    Placement(transformation(origin = {152, -210}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Junctions — node f (degree 4: ring_in, ring_out, sub7, sub8)
  // ---------------------------------------------------------------
  DHNJunction jun_f1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring)
    "Junction f1: splits toward sub7 and remainder" annotation(
    Placement(transformation(origin = {360, 52}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

  DHNJunction jun_f2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction f2: splits toward sub8 and ring_f_g" annotation(
    Placement(transformation(origin = {360, -6}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

  // ---------------------------------------------------------------
  // Junctions — node h (degree 4: ring_in, ring_out, sub9, sub10)
  // ---------------------------------------------------------------
  DHNJunction jun_h1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring)
    "Junction h1: splits toward sub9 and remainder" annotation(
    Placement(transformation(origin = {100, 240}, extent = {{-20, -20}, {20, 20}})));

  DHNJunction jun_h2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction h2: splits toward sub10 and ring_h_src" annotation(
    Placement(transformation(origin = {152, 240}, extent = {{-20, -20}, {20, 20}})));
  
  // ---------------------------------------------------------------
  // Junctions — node c, e, g
  // ---------------------------------------------------------------
  Buildings.Fluid.FixedResistances.PressureDrop junSup_c (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node c" annotation(
    Placement(transformation(origin = {-52, -200}, extent = {{-20, -20}, {20, 20}})));
  
    Buildings.Fluid.FixedResistances.PressureDrop junRet_c (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node c" annotation(
    Placement(transformation(origin = {-52, -220}, extent = {{20, -20}, {-20, 20}})));

  Buildings.Fluid.FixedResistances.PressureDrop junSup_e (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node e" annotation(
    Placement(transformation(origin = {320, -200}, extent = {{-20, -20}, {20, 20}})));
  
  Buildings.Fluid.FixedResistances.PressureDrop junRet_e (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node e" annotation(
    Placement(transformation(origin = {320, -220}, extent = {{20, -20}, {-20, 20}})));

    Buildings.Fluid.FixedResistances.PressureDrop junSup_g (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node g" annotation(
    Placement(transformation(origin = {348, 200}, extent = {{-20, 20}, {20, -20}}, rotation = 90)));

  Buildings.Fluid.FixedResistances.PressureDrop junRet_g (
  redeclare package Medium = Medium,
    m_flow_nominal = m_ring,
    dp_nominal     = 610,
    allowFlowReversal = true)
    "90-deg bend at node g" annotation(
    Placement(transformation(origin = {372, 200}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // ETS substations (10 instances)
  // ---------------------------------------------------------------
  BuildingWithIndirectETS ets[nSub](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam             = filNam,
    each facMul             = 1.0,
    each TDisSup_nominal    = TDisSupSet,
    each THeaWatSup_nominal = THeaWatSup_nominal,
    each THeaWatRet_nominal = THeaWatRet_nominal,
    each dTDis_nominal      = dTDis_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {558, 24}, extent = {{-16, -16}, {16, 16}})));  equation
  
  // ---------------------------------------------------------------
  // Source
  // ---------------------------------------------------------------
  connect(src.port_bDis, jun_src.port_aSupIn) annotation(
    Line(points = {{-180, 244}, {-132, 244}, {-132, 246}}, color = {0, 127, 255}));
  connect(jun_src.port_bRetOut, src.port_aDis) annotation(
    Line(points = {{-132, 234}, {-180, 234}, {-180, 236}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut1, pipe_h_src.port_aDisRet) annotation(
    Line(points = {{-108, 246}, {0, 246}}, color = {0, 127, 255}));
  connect(pipe_h_src.port_bDisSup, jun_src.port_aRetIn1) annotation(
    Line(points = {{0, 234}, {-108, 234}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut2, pipe_src_a.port_aDisSup) annotation(
    Line(points = {{-114, 228}, {-114, 160}}, color = {0, 127, 255}));
  connect(pipe_src_a.port_bDisRet, jun_src.port_aRetIn2) annotation(
    Line(points = {{-126, 160}, {-126, 228}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node a
  // ---------------------------------------------------------------
  connect(pipe_src_a.port_bDisSup, jun_a1.port_aSupIn) annotation(
    Line(points = {{-114, 120}, {-114, 92}}, color = {0, 127, 255}));
  connect(jun_a1.port_bRetOut, pipe_src_a.port_aDisRet) annotation(
    Line(points = {{-126, 92}, {-126, 120}}, color = {0, 127, 255}));
  connect(jun_a1.port_bSupOut2, pipe_a_sub1.port_aDisSup) annotation(
    Line(points = {{-132, 74}, {-180, 74}}, color = {0, 127, 255}));
  connect(pipe_a_sub1.port_bDisRet, jun_a1.port_aRetIn2) annotation(
    Line(points = {{-180, 86}, {-132, 86}}, color = {0, 127, 255}));
  connect(jun_a1.port_bSupOut1, jun_a2.port_aSupIn) annotation(
    Line(points = {{-114, 68}, {-114, 52}}, color = {0, 127, 255}));
  connect(jun_a2.port_bRetOut, jun_a1.port_aRetIn1) annotation(
    Line(points = {{-126, 52}, {-126, 68}}, color = {0, 127, 255}));
  connect(jun_a2.port_bSupOut2, pipe_a_sub2.port_aDisSup) annotation(
    Line(points = {{-132, 34}, {-60, 34}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisRet, jun_a2.port_aRetIn2) annotation(
    Line(points = {{-60, 46}, {-132, 46}}, color = {0, 127, 255}));
  connect(jun_a2.port_bSupOut1, pipe_a_b.port_aDisSup) annotation(
    Line(points = {{-114, 28}, {-114, 6}}, color = {0, 127, 255}));
  connect(pipe_a_b.port_bDisRet, jun_a2.port_aRetIn1) annotation(
    Line(points = {{-126, 6}, {-126, 28}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node b
  // ---------------------------------------------------------------
  connect(pipe_a_b.port_bDisSup, jun_b1.port_aSupIn) annotation(
    Line(points = {{-114, -34}, {-114, -60}}, color = {0, 127, 255}));
  connect(jun_b1.port_bRetOut, pipe_a_b.port_aDisRet) annotation(
    Line(points = {{-126, -60}, {-126, -34}}, color = {0, 127, 255}));
  connect(jun_b1.port_bSupOut2, pipe_b_sub3.port_aDisSup) annotation(
    Line(points = {{-132, -78}, {-180, -78}, {-180, -76}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisRet, jun_b1.port_aRetIn2) annotation(
    Line(points = {{-180, -64}, {-132, -64}, {-132, -66}}, color = {0, 127, 255}));
  connect(jun_b1.port_bSupOut1, jun_b2.port_aSupIn) annotation(
    Line(points = {{-114, -84}, {-114, -100}}, color = {0, 127, 255}));
  connect(jun_b2.port_bRetOut, jun_b1.port_aRetIn1) annotation(
    Line(points = {{-126, -100}, {-126, -84}}, color = {0, 127, 255}));
  connect(jun_b2.port_bSupOut2, pipe_b_sub4.port_aDisSup) annotation(
    Line(points = {{-132, -118}, {-60, -118}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisRet, jun_b2.port_aRetIn2) annotation(
    Line(points = {{-60, -106}, {-132, -106}}, color = {0, 127, 255}));
  connect(jun_b2.port_bSupOut1, pipe_b_c.port_aDisSup) annotation(
    Line(points = {{-114, -124}, {-114, -140}}, color = {0, 127, 255}));
  connect(pipe_b_c.port_bDisRet, jun_b2.port_aRetIn1) annotation(
    Line(points = {{-126, -140}, {-126, -124}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node c
  // ---------------------------------------------------------------
  connect(pipe_b_c.port_bDisSup, junSup_c.port_a) annotation(
    Line(points = {{-114, -180}, {-114, -200}, {-72, -200}}, color = {0, 127, 255}));
  connect(junRet_c.port_b, pipe_b_c.port_aDisRet) annotation(
    Line(points = {{-72, -220}, {-126, -220}, {-126, -180}}, color = {0, 127, 255}));
  connect(junSup_c.port_b, pipe_c_d.port_aDisSup) annotation(
    Line(points = {{-32, -200}, {-14, -200}, {-14, -204}, {0, -204}}, color = {0, 127, 255}));
  connect(pipe_c_d.port_bDisRet, junRet_c.port_a) annotation(
    Line(points = {{0, -216}, {-14, -216}, {-14, -220}, {-32, -220}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node d
  // ---------------------------------------------------------------
  connect(pipe_c_d.port_bDisSup, jun_d1.port_aSupIn) annotation(
    Line(points = {{40, -204}, {88, -204}}, color = {0, 127, 255}));
  connect(jun_d1.port_bRetOut, pipe_c_d.port_aDisRet) annotation(
    Line(points = {{88, -216}, {40, -216}}, color = {0, 127, 255}));
  connect(jun_d1.port_bSupOut2, pipe_d_sub5.port_aDisSup) annotation(
    Line(points = {{106, -222}, {106, -184}}, color = {0, 127, 255}));
  connect(pipe_d_sub5.port_bDisRet, jun_d1.port_aRetIn2) annotation(
    Line(points = {{94, -184}, {94, -222}}, color = {0, 127, 255}));
  connect(jun_d1.port_bSupOut1, jun_d2.port_aSupIn) annotation(
    Line(points = {{112, -204}, {140, -204}}, color = {0, 127, 255}));
  connect(jun_d2.port_bRetOut, jun_d1.port_aRetIn1) annotation(
    Line(points = {{140, -216}, {112, -216}}, color = {0, 127, 255}));
  connect(jun_d2.port_bSupOut2, pipe_d_sub6.port_aDisSup) annotation(
    Line(points = {{158, -222}, {158, -250}}, color = {0, 127, 255}));
  connect(pipe_d_sub6.port_bDisRet, jun_d2.port_aRetIn2) annotation(
    Line(points = {{146, -250}, {146, -222}}, color = {0, 127, 255}));
  connect(jun_d2.port_bSupOut1, pipe_d_e.port_aDisSup) annotation(
    Line(points = {{164, -204}, {200, -204}}, color = {0, 127, 255}));
  connect(pipe_d_e.port_bDisRet, jun_d2.port_aRetIn1) annotation(
    Line(points = {{200, -216}, {164, -216}}, color = {0, 127, 255}));
 
  // ---------------------------------------------------------------
  // Node e
  // ---------------------------------------------------------------
  connect(pipe_d_e.port_bDisSup, junSup_e.port_a) annotation(
    Line(points = {{240, -204}, {274, -204}, {274, -200}, {300, -200}}, color = {0, 127, 255}));
  connect(junRet_e.port_b, pipe_d_e.port_aDisRet) annotation(
    Line(points = {{300, -220}, {274, -220}, {274, -216}, {240, -216}}, color = {0, 127, 255}));
  connect(junSup_e.port_b, pipe_e_f.port_aDisSup) annotation(
    Line(points = {{340, -200}, {354, -200}, {354, -96}}, color = {0, 127, 255}));
  connect(pipe_e_f.port_bDisRet, junRet_e.port_a) annotation(
    Line(points = {{366, -96}, {366, -220}, {340, -220}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node f
  // ---------------------------------------------------------------
  connect(pipe_e_f.port_bDisSup, jun_f2.port_aSupIn) annotation(
    Line(points = {{354, -56}, {354, -18}}, color = {0, 127, 255}));
  connect(jun_f2.port_bRetOut, pipe_e_f.port_aDisRet) annotation(
    Line(points = {{366, -18}, {366, -56}}, color = {0, 127, 255}));
  connect(jun_f2.port_bSupOut2, pipe_f_sub7.port_aDisSup) annotation(
    Line(points = {{372, 0}, {300, 0}}, color = {0, 127, 255}));
  connect(pipe_f_sub7.port_bDisRet, jun_f2.port_aRetIn2) annotation(
    Line(points = {{300, -12}, {372, -12}}, color = {0, 127, 255}));
  connect(jun_f2.port_bSupOut1, jun_f1.port_aSupIn) annotation(
    Line(points = {{354, 6}, {354, 40}}, color = {0, 127, 255}));
  connect(jun_f1.port_bRetOut, jun_f2.port_aRetIn1) annotation(
    Line(points = {{366, 40}, {366, 6}}, color = {0, 127, 255}));
  connect(jun_f1.port_bSupOut2, pipe_f_sub8.port_aDisSup) annotation(
    Line(points = {{372, 58}, {420, 58}}, color = {0, 127, 255}));
  connect(pipe_f_sub8.port_bDisRet, jun_f1.port_aRetIn2) annotation(
    Line(points = {{420, 46}, {372, 46}}, color = {0, 127, 255}));
  connect(jun_f1.port_bSupOut1, pipe_f_g.port_aDisSup) annotation(
    Line(points = {{354, 64}, {354, 100}}, color = {0, 127, 255}));
  connect(pipe_f_g.port_bDisRet, jun_f1.port_aRetIn1) annotation(
    Line(points = {{366, 100}, {366, 64}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node g
  // ---------------------------------------------------------------
  connect(pipe_f_g.port_bDisSup, junSup_g.port_a) annotation(
    Line(points = {{354, 140}, {354, 160}, {348, 160}, {348, 180}}, color = {0, 127, 255}));
  connect(junRet_g.port_b, pipe_f_g.port_aDisRet) annotation(
    Line(points = {{372, 180}, {372, 160}, {366, 160}, {366, 140}}, color = {0, 127, 255}));
  connect(junSup_g.port_b, pipe_g_h.port_aDisSup) annotation(
    Line(points = {{348, 220}, {348, 234}, {240, 234}}, color = {0, 127, 255}));
  connect(pipe_g_h.port_bDisRet, junRet_g.port_a) annotation(
    Line(points = {{240, 246}, {372, 246}, {372, 220}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node h
  // ---------------------------------------------------------------
  connect(pipe_h_src.port_bDisRet, jun_h1.port_aSupIn) annotation(
    Line(points = {{40, 246}, {88, 246}}, color = {0, 127, 255}));
  connect(jun_h1.port_bRetOut, pipe_h_src.port_aDisSup) annotation(
    Line(points = {{88, 234}, {40, 234}}, color = {0, 127, 255}));
  connect(jun_h1.port_bSupOut2, pipe_h_sub9.port_aDisSup) annotation(
    Line(points = {{106, 228}, {106, 280}}, color = {0, 127, 255}));
  connect(pipe_h_sub9.port_bDisRet, jun_h1.port_aRetIn2) annotation(
    Line(points = {{94, 280}, {94, 228}}, color = {0, 127, 255}));
  connect(jun_h1.port_bSupOut1, jun_h2.port_aSupIn) annotation(
    Line(points = {{112, 246}, {140, 246}}, color = {0, 127, 255}));
  connect(jun_h2.port_bRetOut, jun_h1.port_aRetIn1) annotation(
    Line(points = {{140, 234}, {112, 234}}, color = {0, 127, 255}));
  connect(jun_h2.port_bSupOut2, pipe_h_sub10.port_aDisSup) annotation(
    Line(points = {{158, 228}, {158, 200}}, color = {0, 127, 255}));
  connect(pipe_h_sub10.port_bDisRet, jun_h2.port_aRetIn2) annotation(
    Line(points = {{146, 200}, {146, 228}}, color = {0, 127, 255}));
  connect(jun_h2.port_bSupOut1, pipe_g_h.port_aDisRet) annotation(
    Line(points = {{164, 246}, {200, 246}}, color = {0, 127, 255}));
  connect(pipe_g_h.port_bDisSup, jun_h2.port_aRetIn1) annotation(
    Line(points = {{200, 234}, {164, 234}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // ets
  // ---------------------------------------------------------------
  connect(pipe_a_sub1.port_bDisSup, ets[1].port_aSerHea) annotation(
    Line(points = {{-220, 74}, {-260, 74}, {-260, -40}, {520, -40}, {520, 20}, {542, 20}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[1].port_bSerHea, pipe_a_sub1.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -46}, {-240, -46}, {-240, 86}, {-220, 86}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisSup, ets[2].port_aSerHea) annotation(
    Line(points = {{-20, 34}, {0, 34}, {0, -40}, {520, -40}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[2].port_bSerHea, pipe_a_sub2.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -46}, {20, -46}, {20, 46}, {-20, 46}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisSup, ets[3].port_aSerHea) annotation(
    Line(points = {{-220, -76}, {-240, -76}, {-240, -132}, {520, -132}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[3].port_bSerHea, pipe_b_sub3.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -128}, {-262, -128}, {-262, -64}, {-220, -64}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisSup, ets[4].port_aSerHea) annotation(
    Line(points = {{-20, -118}, {520, -118}, {520, 20}, {542, 20}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[4].port_bSerHea, pipe_b_sub4.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -104}, {-20, -104}, {-20, -106}}, color = {0, 127, 255}));
  connect(pipe_d_sub5.port_bDisSup, ets[5].port_aSerHea) annotation(
    Line(points = {{106, -144}, {106, -40}, {520, -40}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[5].port_bSerHea, pipe_d_sub5.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -46}, {94, -46}, {94, -144}}, color = {0, 127, 255}));
  connect(pipe_d_sub6.port_bDisSup, ets[6].port_aSerHea) annotation(
    Line(points = {{158, -290}, {158, -320}, {520, -320}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[6].port_bSerHea, pipe_d_sub6.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, -300}, {146, -300}, {146, -290}}, color = {0, 127, 255}));
  connect(pipe_f_sub7.port_bDisSup, ets[7].port_aSerHea) annotation(
    Line(points = {{260, 0}, {220, 0}, {220, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[7].port_bSerHea, pipe_f_sub7.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, 44}, {500, 44}, {500, 14}, {240, 14}, {240, -12}, {260, -12}}, color = {0, 127, 255}));
  connect(pipe_f_sub8.port_bDisSup, ets[8].port_aSerHea) annotation(
    Line(points = {{460, 58}, {520, 58}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[8].port_bSerHea, pipe_f_sub8.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, 46}, {460, 46}}, color = {0, 127, 255}));
  connect(pipe_h_sub9.port_bDisSup, ets[9].port_aSerHea) annotation(
    Line(points = {{106, 320}, {106, 360}, {520, 360}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[9].port_bSerHea, pipe_h_sub9.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, 340}, {94, 340}, {94, 320}}, color = {0, 127, 255}));
  connect(pipe_h_sub10.port_bDisSup, ets[10].port_aSerHea) annotation(
    Line(points = {{158, 160}, {158, 146}, {520, 146}, {520, 22}, {542, 22}}, color = {0, 127, 255}));
  connect(ets[10].port_bSerHea, pipe_h_sub10.port_aDisRet) annotation(
    Line(points = {{574, 22}, {600, 22}, {600, 152}, {146, 152}, {146, 160}}, color = {0, 127, 255}));
 
 annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    experiment(
      StartTime = 0,
      StopTime  = 604800,
      Tolerance = 1e-06,
      Interval  = 600),
    Diagram(coordinateSystem(extent = {{-350, -350}, {620, 380}})),
    Icon(coordinateSystem(extent = {{-350, -350}, {620, 380}})),
    version = "");
end DHN_THV_3G_L_S_BASE_1;
