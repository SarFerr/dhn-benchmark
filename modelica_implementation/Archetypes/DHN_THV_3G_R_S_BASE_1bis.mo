within modelica_implementation.Archetypes;

model DHN_THV_3G_R_S_BASE_1bis
  "Benchmark network DHN_THV_3G_R_S_BASE
   Thermo-Hydraulic Validation — 3rd Generation District Heating — Radial — Small.
   N=15 nodes (1 source, 4 junctions, 10 substations).
   E=14 pipe segments (4 trunk DN50/DN65 + 10 branch DN25).
   L=0 independent loops (radial tree topology).
   Simulation: 7 days, 10-min resolution (1008 timesteps).
   Control: VF-CT (variable flow, constant temperature), T_sup=80 degC.
  "

  import modelica_implementation.Components.PlantStation;
  import modelica_implementation.Components.DHNJunction;
  import modelica_implementation.Components.DHNPipe;
  import modelica_implementation.Components.DHNBuilding;
  import modelica_implementation.Components.DHNSubstation;

  replaceable package Medium = Buildings.Media.Water
    "District heating medium";

  inner Modelica.Fluid.System system(
    energyDynamics    = Modelica.Fluid.Types.Dynamics.FixedInitial,
    massDynamics      = Modelica.Fluid.Types.Dynamics.FixedInitial,
    allowFlowReversal = false);

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

  parameter Modelica.Units.SI.MassFlowRate m_src_a = 5 * m_sub
    "Trunk src-a nominal flow (serves sub1,2,5,6,7) [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_src_b = 5 * m_sub
    "Trunk src-b nominal flow (serves sub3,4,8,9,10) [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_a_c = 3 * m_sub
    "Trunk a-c nominal flow (serves sub5,6,7) [kg/s]";

  parameter Modelica.Units.SI.MassFlowRate m_b_d = 3 * m_sub
    "Trunk b-d nominal flow (serves sub8,9,10) [kg/s]";

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
    Placement(transformation(origin = {-300, 180}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Source junction
  // ---------------------------------------------------------------
  DHNJunction jun_src(
    redeclare package Medium = Medium,
    m_flow_nominal = m_total)
    "Source junction: splits total flow toward trunk a and trunk b" annotation(
    Placement(transformation(origin = {-228, 180}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Trunk pipes
  // ---------------------------------------------------------------
  DHNPipe pipe_src_a(
    redeclare package Medium = Medium,
    length         = 163.9,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_src_a,
    TGround        = TGround)
    "Trunk src to junction a — DN65, 163.9 m" annotation(
    Placement(transformation(origin = {-230, 100}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_src_b(
    redeclare package Medium = Medium,
    length         = 102.5,
    d_inner        = 0.0717,
    dIns           = 0.03195,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_src_b,
    TGround        = TGround)
    "Trunk src to junction b — DN65, 102.5 m" annotation(
    Placement(transformation(origin = {-160, 180}, extent = {{-20, -20}, {20, 20}})));

  DHNPipe pipe_a_c(
    redeclare package Medium = Medium,
    length         = 127.5,
    d_inner        = 0.0545,
    dIns           = 0.03235,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_a_c,
    TGround        = TGround)
    "Trunk junction a to junction c — DN50, 127.5 m" annotation(
    Placement(transformation(origin = {-228, -80}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_b_d(
    redeclare package Medium = Medium,
    length         = 122.3,
    d_inner        = 0.0545,
    dIns           = 0.03235,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_b_d,
    TGround        = TGround)
    "Trunk junction b to junction d — DN50, 122.3 m" annotation(
    Placement(transformation(origin = {20, 180}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Branch pipes to substations
  // ---------------------------------------------------------------
  DHNPipe pipe_a_sub1(
    redeclare package Medium = Medium,
    length         = 173.6,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch a to sub1 — DN25, 173.6 m" annotation(
    Placement(transformation(origin = {-320, 32}, extent = {{20, 20}, {-20, -20}}, rotation = -0)));

  DHNPipe pipe_a_sub2(
    redeclare package Medium = Medium,
    length         = 167.7,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch a to sub2 — DN25, 167.7 m" annotation(
    Placement(transformation(origin = {-140, -8}, extent = {{-20, 20}, {20, -20}}, rotation = -0)));

  DHNPipe pipe_b_sub3(
    redeclare package Medium = Medium,
    length         = 189.2,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch b to sub3 — DN25, 189.2 m" annotation(
    Placement(transformation(origin = {-88, 240}, extent = {{20, -20}, {-20, 20}}, rotation = -90)));

  DHNPipe pipe_b_sub4(
    redeclare package Medium = Medium,
    length         = 108.7,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch b to sub4 — DN25, 108.7 m" annotation(
    Placement(transformation(origin = {-48, 120}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_c_sub5(
    redeclare package Medium = Medium,
    length         = 142.2,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch c to sub5 — DN25, 142.2 m" annotation(
    Placement(transformation(origin = {-320, -148}, extent = {{20, 20}, {-20, -20}}, rotation = -0)));

  DHNPipe pipe_c_sub6(
    redeclare package Medium = Medium,
    length         = 103.0,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch c to sub6 — DN25, 103.0 m" annotation(
    Placement(transformation(origin = {-140, -188}, extent = {{-20, 20}, {20, -20}}, rotation = -0)));

  DHNPipe pipe_c_sub7(
    redeclare package Medium = Medium,
    length         = 121.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch c to sub7 — DN25, 121.9 m" annotation(
    Placement(transformation(origin = {-228, -260}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_d_sub8(
    redeclare package Medium = Medium,
    length         = 150.5,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch d to sub8 — DN25, 150.5 m" annotation(
    Placement(transformation(origin = {132, 120}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNPipe pipe_d_sub9(
    redeclare package Medium = Medium,
    length         = 102.7,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch d to sub9 — DN25, 102.7 m" annotation(
    Placement(transformation(origin = {92, 240}, extent = {{20, -20}, {-20, 20}}, rotation = -90)));

  DHNPipe pipe_d_sub10(
    redeclare package Medium = Medium,
    length         = 119.9,
    d_inner        = 0.0282,
    dIns           = 0.02815,
    kIns           = 0.033,
    roughness      = 4.5e-5,
    m_flow_nominal = m_sub,
    TGround        = TGround)
    "Branch d to sub10 — DN25, 119.9 m" annotation(
    Placement(transformation(origin = {200, 180}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Junctions — node a (degree 4)
  // ---------------------------------------------------------------
  DHNJunction jun_a1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_src_a)
    "Junction a1: splits toward sub1 and remainder" annotation(
    Placement(transformation(origin = {-228, 28}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNJunction jun_a2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_src_a - m_sub)
    "Junction a2: splits toward sub2 and trunk a-c" annotation(
    Placement(transformation(origin = {-228, -10}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // Junctions — node b (degree 4)
  // ---------------------------------------------------------------
  DHNJunction jun_b1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_src_b)
    "Junction b1: splits toward sub3 and remainder" annotation(
    Placement(transformation(origin = {-88, 180}, extent = {{-20, -20}, {20, 20}}, rotation = -0)));

  DHNJunction jun_b2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_src_b - m_sub)
    "Junction b2: splits toward sub4 and trunk b-d" annotation(
    Placement(transformation(origin = {-48, 180}, extent = {{-20, -20}, {20, 20}})));

  // ---------------------------------------------------------------
  // Junctions — node c (degree 4)
  // ---------------------------------------------------------------
  DHNJunction jun_c1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_a_c)
    "Junction c1: splits toward sub5 and remainder" annotation(
    Placement(transformation(origin = {-228, -148}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  DHNJunction jun_c2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_a_c - m_sub)
    "Junction c2: splits toward sub6 and sub7" annotation(
    Placement(transformation(origin = {-228, -190}, extent = {{-20, -20}, {20, 20}}, rotation = -90)));

  // ---------------------------------------------------------------
  // Junctions — node d (degree 4)
  // ---------------------------------------------------------------
  DHNJunction jun_d1(
    redeclare package Medium = Medium,
    m_flow_nominal = m_b_d)
    "Junction d1: splits toward sub8 and remainder" annotation(
    Placement(transformation(origin = {92, 180}, extent = {{-20, -20}, {20, 20}})));

  DHNJunction jun_d2(
    redeclare package Medium = Medium,
    m_flow_nominal = m_b_d - m_sub)
    "Junction d2: splits toward sub9 and sub10" annotation(
    Placement(transformation(origin = {132, 180}, extent = {{-20, -20}, {20, 20}}, rotation = -0)));

  // ---------------------------------------------------------------
  // ETS substations (10 instances, identical parameters)
  // ---------------------------------------------------------------
  DHNBuilding ets[nSub](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam            = filNam,
    each Q_flow_nominal    = Q_peak_sub,
    each mDis_flow_nominal = m_sub,
    each mBui_flow_nominal = m_sub,
    each TDisSup_nominal   = TDisSupSet,
    each THeaWatRet_nominal = THeaWatRet_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {296, 4}, extent = {{-16,-16},{16,16}})));

equation
  
  // ---------------------------------------------------------------
  // Source
  // ---------------------------------------------------------------
  connect(src.port_bDis, jun_src.port_aSupIn) annotation(
    Line(points = {{-280, 184}, {-240, 184}, {-240, 186}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut2, pipe_src_a.port_aDisSup) annotation(
    Line(points = {{-222, 168}, {-224, 168}, {-224, 120}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut1, pipe_src_b.port_aDisSup) annotation(
    Line(points = {{-216, 186}, {-180, 186}}, color = {0, 127, 255}));
  connect(pipe_src_a.port_bDisRet, jun_src.port_aRetIn2) annotation(
    Line(points = {{-236, 120}, {-234, 120}, {-234, 168}}, color = {0, 127, 255}));
  connect(pipe_src_b.port_bDisRet, jun_src.port_aRetIn1) annotation(
    Line(points = {{-180, 174}, {-216, 174}}, color = {0, 127, 255}));
  connect(jun_src.port_bRetOut, src.port_aDis) annotation(
    Line(points = {{-240.4, 174}, {-280.4, 174}, {-280.4, 176}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node a
  // ---------------------------------------------------------------
  connect(pipe_src_a.port_bDisSup, jun_a1.port_aSupIn) annotation(
    Line(points = {{-224, 80}, {-222, 80}, {-222, 40}}, color = {0, 127, 255}));
  connect(jun_a1.port_bRetOut, pipe_src_a.port_aDisRet) annotation(
    Line(points = {{-234, 40}, {-236, 40}, {-236, 80}}, color = {0, 127, 255}));
  connect(jun_a1.port_bSupOut2, pipe_a_sub1.port_aDisSup) annotation(
    Line(points = {{-240, 22}, {-300, 22}, {-300, 26}}, color = {0, 127, 255}));
  connect(pipe_a_sub1.port_bDisRet, jun_a1.port_aRetIn2) annotation(
    Line(points = {{-300, 38}, {-240, 38}, {-240, 34}}, color = {0, 127, 255}));
  connect(jun_a1.port_bSupOut1, jun_a2.port_aSupIn) annotation(
    Line(points = {{-222, 16}, {-222, 2}}, color = {0, 127, 255}));
  connect(jun_a2.port_bRetOut, jun_a1.port_aRetIn1) annotation(
    Line(points = {{-234, 2}, {-234, 16}}, color = {0, 127, 255}));
  connect(jun_a2.port_bSupOut2, pipe_a_sub2.port_aDisSup) annotation(
    Line(points = {{-240, -16}, {-160, -16}, {-160, -14}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisRet, jun_a2.port_aRetIn2) annotation(
    Line(points = {{-160, -2}, {-240, -2}, {-240, -4}}, color = {0, 127, 255}));
  connect(jun_a2.port_bSupOut1, pipe_a_c.port_aDisSup) annotation(
    Line(points = {{-222, -22}, {-222, -60}}, color = {0, 127, 255}));
  connect(pipe_a_c.port_bDisRet, jun_a2.port_aRetIn1) annotation(
    Line(points = {{-234, -60}, {-234, -22}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node c
  // ---------------------------------------------------------------
  connect(pipe_a_c.port_bDisSup, jun_c1.port_aSupIn) annotation(
    Line(points = {{-222, -100}, {-222, -136}}, color = {0, 127, 255}));
  connect(jun_c1.port_bRetOut, pipe_a_c.port_aDisRet) annotation(
    Line(points = {{-234, -136}, {-234, -100}}, color = {0, 127, 255}));
  connect(jun_c1.port_bSupOut2, pipe_c_sub5.port_aDisSup) annotation(
    Line(points = {{-240, -154}, {-300, -154}}, color = {0, 127, 255}));
  connect(pipe_c_sub5.port_bDisRet, jun_c1.port_aRetIn2) annotation(
    Line(points = {{-300, -142}, {-240, -142}}, color = {0, 127, 255}));
  connect(jun_c1.port_bSupOut1, jun_c2.port_aSupIn) annotation(
    Line(points = {{-222, -160}, {-222, -178}}, color = {0, 127, 255}));
  connect(jun_c2.port_bRetOut, jun_c1.port_aRetIn1) annotation(
    Line(points = {{-234, -178}, {-234, -160}}, color = {0, 127, 255}));
  connect(jun_c2.port_bSupOut2, pipe_c_sub6.port_aDisSup) annotation(
    Line(points = {{-240, -196}, {-160, -196}, {-160, -194}}, color = {0, 127, 255}));
  connect(pipe_c_sub6.port_bDisRet, jun_c2.port_aRetIn2) annotation(
    Line(points = {{-160, -182}, {-240, -182}, {-240, -184}}, color = {0, 127, 255}));
  connect(jun_c2.port_bSupOut1, pipe_c_sub7.port_aDisSup) annotation(
    Line(points = {{-222, -202}, {-222, -240}}, color = {0, 127, 255}));
  connect(pipe_c_sub7.port_bDisRet, jun_c2.port_aRetIn1) annotation(
    Line(points = {{-234, -240}, {-234, -202}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node b
  // ---------------------------------------------------------------
  connect(pipe_src_b.port_bDisSup, jun_b1.port_aSupIn) annotation(
    Line(points = {{-140, 186}, {-100, 186}}, color = {0, 127, 255}));
  connect(jun_b1.port_bRetOut, pipe_src_b.port_aDisRet) annotation(
    Line(points = {{-100, 174}, {-140, 174}}, color = {0, 127, 255}));
  connect(jun_b1.port_bSupOut2, pipe_b_sub3.port_aDisSup) annotation(
    Line(points = {{-82, 168}, {-82, 220}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisRet, jun_b1.port_aRetIn2) annotation(
    Line(points = {{-94, 220}, {-94, 168}}, color = {0, 127, 255}));
  connect(jun_b1.port_bSupOut1, jun_b2.port_aSupIn) annotation(
    Line(points = {{-76, 186}, {-60, 186}}, color = {0, 127, 255}));
  connect(jun_b2.port_bRetOut, jun_b1.port_aRetIn1) annotation(
    Line(points = {{-60, 174}, {-76, 174}}, color = {0, 127, 255}));
  connect(jun_b2.port_bSupOut2, pipe_b_sub4.port_aDisSup) annotation(
    Line(points = {{-42, 168}, {-42, 140}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisRet, jun_b2.port_aRetIn2) annotation(
    Line(points = {{-54, 140}, {-54, 168}}, color = {0, 127, 255}));
  connect(jun_b2.port_bSupOut1, pipe_b_d.port_aDisSup) annotation(
    Line(points = {{-36, 186}, {0, 186}}, color = {0, 127, 255}));
  connect(pipe_b_d.port_bDisRet, jun_b2.port_aRetIn1) annotation(
    Line(points = {{0, 174}, {-36, 174}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node d
  // ---------------------------------------------------------------
  connect(pipe_b_d.port_bDisSup, jun_d1.port_aSupIn) annotation(
    Line(points = {{40, 186}, {80, 186}}, color = {0, 127, 255}));
  connect(jun_d1.port_bRetOut, pipe_b_d.port_aDisRet) annotation(
    Line(points = {{80, 174}, {40, 174}}, color = {0, 127, 255}));
  connect(jun_d1.port_bSupOut2, pipe_d_sub9.port_aDisSup) annotation(
    Line(points = {{98, 168}, {98, 220}}, color = {0, 127, 255}));
  connect(pipe_d_sub9.port_bDisRet, jun_d1.port_aRetIn2) annotation(
    Line(points = {{86, 220}, {86, 168}}, color = {0, 127, 255}));
  connect(jun_d1.port_bSupOut1, jun_d2.port_aSupIn) annotation(
    Line(points = {{104, 186}, {120, 186}}, color = {0, 127, 255}));
  connect(jun_d2.port_bRetOut, jun_d1.port_aRetIn1) annotation(
    Line(points = {{120, 174}, {104, 174}}, color = {0, 127, 255}));
  connect(jun_d2.port_bSupOut2, pipe_d_sub8.port_aDisSup) annotation(
    Line(points = {{138, 168}, {138, 140}}, color = {0, 127, 255}));
  connect(pipe_d_sub8.port_bDisRet, jun_d2.port_aRetIn2) annotation(
    Line(points = {{126, 140}, {126, 168}}, color = {0, 127, 255}));
  connect(jun_d2.port_bSupOut1, pipe_d_sub10.port_aDisSup) annotation(
    Line(points = {{144, 186}, {180, 186}}, color = {0, 127, 255}));
  connect(pipe_d_sub10.port_bDisRet, jun_d2.port_aRetIn1) annotation(
    Line(points = {{180, 174}, {144, 174}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Branch pipes → ETS substations
  // ---------------------------------------------------------------
  connect(pipe_a_sub1.port_bDisSup, ets[1].port_aSerHea) annotation(
    Line(points = {{-340, 26}, {-360, 26}, {-360, -40}, {240, -40}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[1].port_bSerHea, pipe_a_sub1.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, -30}, {-380, -30}, {-380, 38}, {-340, 38}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisSup, ets[2].port_aSerHea) annotation(
    Line(points = {{-120, -14}, {240, -14}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[2].port_bSerHea, pipe_a_sub2.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, -30}, {-100, -30}, {-100, -2}, {-120, -2}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisSup, ets[3].port_aSerHea) annotation(
    Line(points = {{-82, 260}, {-82, 280}, {240, 280}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[3].port_bSerHea, pipe_b_sub3.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, 272}, {-94, 272}, {-94, 260}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisSup, ets[4].port_aSerHea) annotation(
    Line(points = {{-42, 100}, {-42, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[4].port_bSerHea, pipe_b_sub4.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, 80}, {-54, 80}, {-54, 100}}, color = {0, 127, 255}));
  connect(pipe_c_sub5.port_bDisSup, ets[5].port_aSerHea) annotation(
    Line(points = {{-340, -154}, {-358, -154}, {-358, -220}, {240, -220}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[5].port_bSerHea, pipe_c_sub5.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, -212}, {-380, -212}, {-380, -142}, {-340, -142}}, color = {0, 127, 255}));
  connect(pipe_c_sub6.port_bDisSup, ets[6].port_aSerHea) annotation(
    Line(points = {{-120, -194}, {240, -194}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[6].port_bSerHea, pipe_c_sub6.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, -182}, {-120, -182}}, color = {0, 127, 255}));
  connect(pipe_c_sub7.port_bDisSup, ets[7].port_aSerHea) annotation(
    Line(points = {{-222, -280}, {-222, -290}, {240, -290}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[7].port_bSerHea, pipe_c_sub7.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, -284}, {-234, -284}, {-234, -280}}, color = {0, 127, 255}));
  connect(pipe_d_sub8.port_bDisSup, ets[8].port_aSerHea) annotation(
    Line(points = {{138, 100}, {138, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[8].port_bSerHea, pipe_d_sub8.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, 80}, {126, 80}, {126, 100}}, color = {0, 127, 255}));
  connect(pipe_d_sub9.port_bDisSup, ets[9].port_aSerHea) annotation(
    Line(points = {{98, 260}, {98, 280}, {240, 280}, {240, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[9].port_bSerHea, pipe_d_sub9.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, 272}, {86, 272}, {86, 260}}, color = {0, 127, 255}));
  connect(pipe_d_sub10.port_bDisSup, ets[10].port_aSerHea) annotation(
    Line(points = {{220, 186}, {260, 186}, {260, 2}, {280, 2}}, color = {0, 127, 255}));
  connect(ets[10].port_bSerHea, pipe_d_sub10.port_aDisRet) annotation(
    Line(points = {{312, 2}, {340, 2}, {340, 174}, {220, 174}}, color = {0, 127, 255}));
  
  annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    experiment(
      StartTime = 0,
      StopTime  = 604800,
      Tolerance = 1e-06,
      Interval  = 600),
    Diagram(coordinateSystem(extent = {{-400, -300}, {400, 300}})),
    Icon(coordinateSystem(extent = {{-400, -300}, {400, 300}})),
    version = "");
end DHN_THV_3G_R_S_BASE_1bis;
