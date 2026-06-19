within modelica_implementation.Archetypes;

model DHN_THV_3G_L_S_BASE
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
    energyDynamics    = Modelica.Fluid.Types.Dynamics.FixedInitial,
    massDynamics      = Modelica.Fluid.Types.Dynamics.FixedInitial,
    allowFlowReversal = true);

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
    Placement(transformation(origin = {20, 240}, extent = {{20, -20}, {-20, 20}})));

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
    Placement(transformation(origin = {-240, 100}, extent = {{20, -20}, {-20, 20}})));

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
    Placement(transformation(origin = {0, 100}, extent = {{-20, -20}, {20, 20}})));

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
    Placement(transformation(origin = {-200, -70}, extent = {{20, -20}, {-20, 20}})));

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
    Placement(transformation(origin = {-40, -110}, extent = {{-20, -20}, {20, 20}})));

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
    Placement(transformation(origin = {100, -150}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

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
    Placement(transformation(origin = {280, 52}, extent = {{20, -20}, {-20, 20}})));

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
    Placement(transformation(origin = {440, -6}, extent = {{-20, -20}, {20, 20}})));

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
    Placement(transformation(origin = {100, 300}, extent = {{-20, -20}, {20, 20}}, rotation = 90)));

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
    Placement(transformation(origin = {360, 52}, extent = {{-20, -20}, {20, 20}})));

  DHNJunction jun_f2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_ring - m_sub)
    "Junction f2: splits toward sub8 and ring_f_g" annotation(
    Placement(transformation(origin = {360, -6}, extent = {{-20, -20}, {20, 20}})));

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
    Placement(transformation(origin = {560, 40}, extent = {{-16, -16}, {16, 16}})));

equation

  // ---------------------------------------------------------------
  // Plant → source junction
  // ---------------------------------------------------------------
  connect(src.port_bDis,        jun_src.port_aSupIn);
  connect(jun_src.port_bSupOut1, pipe_src_a.port_aDisSup);
  connect(jun_src.port_bSupOut2, pipe_h_src.port_bDisSup);
  connect(pipe_src_a.port_bDisRet, jun_src.port_aRetIn1);
  connect(pipe_h_src.port_bDisRet, jun_src.port_aRetIn2);
  connect(jun_src.port_bRetOut,  src.port_aDis);

  // ---------------------------------------------------------------
  // Ring: src_a → node a
  // ---------------------------------------------------------------
  connect(pipe_src_a.port_bDisSup,  jun_a1.port_aSupIn);
  connect(jun_a1.port_bRetOut,      pipe_src_a.port_aDisRet);
  connect(jun_a1.port_bSupOut2,     pipe_a_sub1.port_aDisSup);
  connect(pipe_a_sub1.port_bDisRet, jun_a1.port_aRetIn2);
  connect(jun_a1.port_bSupOut1,     jun_a2.port_aSupIn);
  connect(jun_a2.port_bRetOut,      jun_a1.port_aRetIn1);
  connect(jun_a2.port_bSupOut2,     pipe_a_sub2.port_aDisSup);
  connect(pipe_a_sub2.port_bDisRet, jun_a2.port_aRetIn2);
  connect(jun_a2.port_bSupOut1,     pipe_a_b.port_aDisSup);
  connect(pipe_a_b.port_bDisRet,    jun_a2.port_aRetIn1);

  // ---------------------------------------------------------------
  // Ring: a_b → node b
  // ---------------------------------------------------------------
  connect(pipe_a_b.port_bDisSup,    jun_b1.port_aSupIn);
  connect(jun_b1.port_bRetOut,      pipe_a_b.port_aDisRet);
  connect(jun_b1.port_bSupOut2,     pipe_b_sub3.port_aDisSup);
  connect(pipe_b_sub3.port_bDisRet, jun_b1.port_aRetIn2);
  connect(jun_b1.port_bSupOut1,     jun_b2.port_aSupIn);
  connect(jun_b2.port_bRetOut,      jun_b1.port_aRetIn1);
  connect(jun_b2.port_bSupOut2,     pipe_b_sub4.port_aDisSup);
  connect(pipe_b_sub4.port_bDisRet, jun_b2.port_aRetIn2);
  connect(jun_b2.port_bSupOut1,     pipe_b_c.port_aDisSup);
  connect(pipe_b_c.port_bDisRet,    jun_b2.port_aRetIn1);

  // ---------------------------------------------------------------
  // Ring: b_c → c → c_d (node c has degree 2, no ETS)
  // ---------------------------------------------------------------
  connect(pipe_b_c.port_bDisSup,  pipe_c_d.port_aDisSup);
  connect(pipe_c_d.port_bDisRet,  pipe_b_c.port_aDisRet);

  // ---------------------------------------------------------------
  // Ring: c_d → node d
  // ---------------------------------------------------------------
  connect(pipe_c_d.port_bDisSup,    jun_d1.port_aSupIn);
  connect(jun_d1.port_bRetOut,      pipe_c_d.port_aDisRet);
  connect(jun_d1.port_bSupOut2,     pipe_d_sub5.port_aDisSup);
  connect(pipe_d_sub5.port_bDisRet, jun_d1.port_aRetIn2);
  connect(jun_d1.port_bSupOut1,     jun_d2.port_aSupIn);
  connect(jun_d2.port_bRetOut,      jun_d1.port_aRetIn1);
  connect(jun_d2.port_bSupOut2,     pipe_d_sub6.port_aDisSup);
  connect(pipe_d_sub6.port_bDisRet, jun_d2.port_aRetIn2);
  connect(jun_d2.port_bSupOut1,     pipe_d_e.port_aDisSup);
  connect(pipe_d_e.port_bDisRet,    jun_d2.port_aRetIn1);

  // ---------------------------------------------------------------
  // Ring: d_e → e → e_f (node e has degree 2, no ETS)
  // ---------------------------------------------------------------
  connect(pipe_d_e.port_bDisSup,  pipe_e_f.port_aDisSup);
  connect(pipe_e_f.port_bDisRet,  pipe_d_e.port_aDisRet);

  // ---------------------------------------------------------------
  // Ring: e_f → node f
  // ---------------------------------------------------------------
  connect(pipe_e_f.port_bDisSup,    jun_f1.port_aSupIn);
  connect(jun_f1.port_bRetOut,      pipe_e_f.port_aDisRet);
  connect(jun_f1.port_bSupOut2,     pipe_f_sub7.port_aDisSup);
  connect(pipe_f_sub7.port_bDisRet, jun_f1.port_aRetIn2);
  connect(jun_f1.port_bSupOut1,     jun_f2.port_aSupIn);
  connect(jun_f2.port_bRetOut,      jun_f1.port_aRetIn1);
  connect(jun_f2.port_bSupOut2,     pipe_f_sub8.port_aDisSup);
  connect(pipe_f_sub8.port_bDisRet, jun_f2.port_aRetIn2);
  connect(jun_f2.port_bSupOut1,     pipe_f_g.port_aDisSup);
  connect(pipe_f_g.port_bDisRet,    jun_f2.port_aRetIn1);

  // ---------------------------------------------------------------
  // Ring: f_g → g → g_h (node g has degree 2, no ETS)
  // ---------------------------------------------------------------
  connect(pipe_f_g.port_bDisSup,  pipe_g_h.port_aDisSup);
  connect(pipe_g_h.port_bDisRet,  pipe_f_g.port_aDisRet);

  // ---------------------------------------------------------------
  // Ring: g_h → node h
  // ---------------------------------------------------------------
  connect(pipe_g_h.port_bDisSup,     jun_h1.port_aSupIn);
  connect(jun_h1.port_bRetOut,       pipe_g_h.port_aDisRet);
  connect(jun_h1.port_bSupOut2,      pipe_h_sub9.port_aDisSup);
  connect(pipe_h_sub9.port_bDisRet,  jun_h1.port_aRetIn2);
  connect(jun_h1.port_bSupOut1,      jun_h2.port_aSupIn);
  connect(jun_h2.port_bRetOut,       jun_h1.port_aRetIn1);
  connect(jun_h2.port_bSupOut2,      pipe_h_sub10.port_aDisSup);
  connect(pipe_h_sub10.port_bDisRet, jun_h2.port_aRetIn2);
  connect(jun_h2.port_bSupOut1,      pipe_h_src.port_aDisSup);
  connect(pipe_h_src.port_bDisRet,   jun_h2.port_aRetIn1);

  // ---------------------------------------------------------------
  // Branch pipes → ETS substations
  // ---------------------------------------------------------------
  connect(pipe_a_sub1.port_bDisSup,  ets[1].port_aSerHea);
  connect(ets[1].port_bSerHea,       pipe_a_sub1.port_aDisRet);

  connect(pipe_a_sub2.port_bDisSup,  ets[2].port_aSerHea);
  connect(ets[2].port_bSerHea,       pipe_a_sub2.port_aDisRet);

  connect(pipe_b_sub3.port_bDisSup,  ets[3].port_aSerHea);
  connect(ets[3].port_bSerHea,       pipe_b_sub3.port_aDisRet);

  connect(pipe_b_sub4.port_bDisSup,  ets[4].port_aSerHea);
  connect(ets[4].port_bSerHea,       pipe_b_sub4.port_aDisRet);

  connect(pipe_d_sub5.port_bDisSup,  ets[5].port_aSerHea);
  connect(ets[5].port_bSerHea,       pipe_d_sub5.port_aDisRet);

  connect(pipe_d_sub6.port_bDisSup,  ets[6].port_aSerHea);
  connect(ets[6].port_bSerHea,       pipe_d_sub6.port_aDisRet);

  connect(pipe_f_sub7.port_bDisSup,  ets[7].port_aSerHea);
  connect(ets[7].port_bSerHea,       pipe_f_sub7.port_aDisRet);

  connect(pipe_f_sub8.port_bDisSup,  ets[8].port_aSerHea);
  connect(ets[8].port_bSerHea,       pipe_f_sub8.port_aDisRet);

  connect(pipe_h_sub9.port_bDisSup,  ets[9].port_aSerHea);
  connect(ets[9].port_bSerHea,       pipe_h_sub9.port_aDisRet);

  connect(pipe_h_sub10.port_bDisSup, ets[10].port_aSerHea);
  connect(ets[10].port_bSerHea,      pipe_h_sub10.port_aDisRet);

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
end DHN_THV_3G_L_S_BASE;
