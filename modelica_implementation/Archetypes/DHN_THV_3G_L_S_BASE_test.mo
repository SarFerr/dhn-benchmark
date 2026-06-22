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
  DHNPipe pipe_a_sub1(
    redeclare package Medium = Medium,
    length = 103.0, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch a→sub1 — DN25" annotation(
    Placement(transformation(origin = {-80, 60}, extent = {{20, 20}, {-20, -20}})));

  DHNPipe pipe_a_sub2(
    redeclare package Medium = Medium,
    length = 121.9, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch a→sub2 — DN25" annotation(
    Placement(transformation(origin = {80, 60}, extent = {{-20,-20},{20,20}})));

  DHNPipe pipe_b_sub3(
    redeclare package Medium = Medium,
    length = 150.5, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch b→sub3 — DN25" annotation(
    Placement(transformation(origin = {-80, 140}, extent = {{20, 20}, {-20, -20}})));

  DHNPipe pipe_b_sub4(
    redeclare package Medium = Medium,
    length = 102.7, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch b→sub4 — DN25" annotation(
    Placement(transformation(origin = {80, 140}, extent = {{-20,-20},{20,20}})));

  DHNPipe pipe_d_sub5(
    redeclare package Medium = Medium,
    length = 119.9, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch d→sub5 — DN25" annotation(
    Placement(transformation(origin = {-80, 220}, extent = {{20, 20}, {-20, -20}})));

  DHNPipe pipe_d_sub6(
    redeclare package Medium = Medium,
    length = 165.0, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch d→sub6 — DN25" annotation(
    Placement(transformation(origin = {80, 220}, extent = {{-20,-20},{20,20}})));

  DHNPipe pipe_f_sub7(
    redeclare package Medium = Medium,
    length = 154.5, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch f→sub7 — DN25" annotation(
    Placement(transformation(origin = {-80, 300}, extent = {{20, 20}, {-20, -20}})));

  DHNPipe pipe_f_sub8(
    redeclare package Medium = Medium,
    length = 122.0, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch f→sub8 — DN25" annotation(
    Placement(transformation(origin = {80, 300}, extent = {{-20,-20},{20,20}})));

  DHNPipe pipe_h_sub9(
    redeclare package Medium = Medium,
    length = 158.9, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch h→sub9 — DN25" annotation(
    Placement(transformation(origin = {-80, 380}, extent = {{-20,-20},{20,20}})));

  DHNPipe pipe_h_sub10(
    redeclare package Medium = Medium,
    length = 180.9, d_inner = 0.0282, dIns = 0.02815,
    kIns = 0.033, roughness = 4.5e-5,
    m_flow_nominal = m_sub, TGround = TGround)
    "Branch h→sub10 — DN25" annotation(
    Placement(transformation(origin = {80, 380}, extent = {{-20,-20},{20,20}})));

  // ---------------------------------------------------------------
  // Junctions at each connection node (2 ETS in parallel)
  // ---------------------------------------------------------------
    DHNJunction jun_a(
    redeclare package Medium = Medium,
    m_flow_nominal = 2 * m_sub)
    "Junction node a: 1 ring inlet → 2 branch outlets (sub1, sub2)" annotation(
    Placement(transformation(origin = {0, 60}, extent = {{-20,-20},{20,20}})));

  DHNJunction jun_b(
    redeclare package Medium = Medium,
    m_flow_nominal = 2 * m_sub)
    "Junction node b: 1 ring inlet → 2 branch outlets (sub3, sub4)" annotation(
    Placement(transformation(origin = {0, 140}, extent = {{-20,-20},{20,20}})));

  DHNJunction jun_d(
    redeclare package Medium = Medium,
    m_flow_nominal = 2 * m_sub)
    "Junction node d: 1 ring inlet → 2 branch outlets (sub5, sub6)" annotation(
    Placement(transformation(origin = {0, 220}, extent = {{-20,-20},{20,20}})));

  DHNJunction jun_f(
    redeclare package Medium = Medium,
    m_flow_nominal = 2 * m_sub)
    "Junction node f: 1 ring inlet → 2 branch outlets (sub7, sub8)" annotation(
    Placement(transformation(origin = {0, 300}, extent = {{-20,-20},{20,20}})));

  DHNJunction jun_h(
    redeclare package Medium = Medium,
    m_flow_nominal = 2 * m_sub)
    "Junction node h: 1 ring inlet → 2 branch outlets (sub9, sub10)" annotation(
    Placement(transformation(origin = {0, 380}, extent = {{-20,-20},{20,20}})));

equation
  
  // ---------------------------------------------------------------
  // Ring distribution
  // ---------------------------------------------------------------
  connect(src.port_bDis, dis.port_aDisSup) annotation(
    Line(points = {{-200, -16}, {-40, -16}, {-40, -14}}, color = {0, 127, 255}));
  connect(dis.port_bDisRet, src.port_aDis) annotation(
    Line(points = {{-40, -26}, {-200, -26}, {-200, -24}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Ground temperature → distribution network
  // ---------------------------------------------------------------
  connect(TGroDis.port, dis.heatPortsDis) annotation(
    Line(points = {{-150, -60}, {-60, -60}, {-60, -4}, {16, -4}, {16, -10}}, color = {191, 0, 0}, thickness = 0.5));
  connect(TGroRet.port, dis.heatPortsRet) annotation(
    Line(points = {{-150, -100}, {-14, -100}, {-14, -30}}, color = {191, 0, 0}, thickness = 0.5));
  
  // ---------------------------------------------------------------
  // Node a (con[1]) → sub1, sub2
  // ---------------------------------------------------------------
  connect(dis.ports_bCon[1], jun_a.port_aSupIn) annotation(
    Line(points = {{-24, 6}, {-24, 20}, {-6, 20}, {-6, 48}}, color = {0, 127, 255}));
  connect(jun_a.port_bSupOut2, pipe_a_sub1.port_aDisSup) annotation(
    Line(points = {{-12, 54}, {-60, 54}}, color = {0, 127, 255}));
  connect(pipe_a_sub1.port_bDisRet, jun_a.port_aRetIn2) annotation(
    Line(points = {{-60, 66}, {-12, 66}}, color = {0, 127, 255}));
  connect(jun_a.port_bSupOut1, pipe_a_sub2.port_aDisSup) annotation(
    Line(points = {{12, 66}, {60, 66}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisRet, jun_a.port_aRetIn1) annotation(
    Line(points = {{60, 54}, {12, 54}}, color = {0, 127, 255}));
  connect(jun_a.port_bRetOut, dis.ports_aCon[1]) annotation(
    Line(points = {{6, 48}, {6, 20}, {24, 20}, {24, 6}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Node b (con[2]) → sub3, sub4
  // ---------------------------------------------------------------
  connect(dis.ports_bCon[2], jun_b.port_aSupIn) annotation(
    Line(points = {{-24, 6}, {-24, 100}, {-6, 100}, {-6, 128}}, color = {0, 127, 255}));
  connect(jun_b.port_bSupOut2, pipe_b_sub3.port_aDisSup) annotation(
    Line(points = {{-12, 134}, {-60, 134}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisRet, jun_b.port_aRetIn2) annotation(
    Line(points = {{-60, 146}, {-12, 146}}, color = {0, 127, 255}));
  connect(jun_b.port_bSupOut1, pipe_b_sub4.port_aDisSup) annotation(
    Line(points = {{12, 146}, {60, 146}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisRet, jun_b.port_aRetIn1) annotation(
    Line(points = {{60, 134}, {12, 134}}, color = {0, 127, 255}));
  connect(jun_b.port_bRetOut, dis.ports_aCon[2]) annotation(
    Line(points = {{6, 128}, {8, 128}, {8, 100}, {24, 100}, {24, 6}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node d (con[3]) → sub5, sub6
  // ---------------------------------------------------------------
  connect(dis.ports_bCon[3], jun_d.port_aSupIn) annotation(
    Line(points = {{-24, 6}, {-24, 180}, {-6, 180}, {-6, 208}}, color = {0, 127, 255}));
  connect(jun_d.port_bSupOut2, pipe_d_sub5.port_aDisSup) annotation(
    Line(points = {{-12, 214}, {-60, 214}}, color = {0, 127, 255}));
  connect(pipe_d_sub5.port_bDisRet, jun_d.port_aRetIn2) annotation(
    Line(points = {{-60, 226}, {-12, 226}}, color = {0, 127, 255}));
  connect(jun_d.port_bSupOut1, pipe_d_sub6.port_aDisSup) annotation(
    Line(points = {{12, 226}, {60, 226}}, color = {0, 127, 255}));
  connect(pipe_d_sub6.port_bDisRet, jun_d.port_aRetIn1) annotation(
    Line(points = {{60, 214}, {12, 214}}, color = {0, 127, 255}));
  connect(jun_d.port_bRetOut, dis.ports_aCon[3]) annotation(
    Line(points = {{6, 208}, {6, 180}, {24, 180}, {24, 6}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node f (con[4]) → sub7, sub8
  // ---------------------------------------------------------------
  connect(dis.ports_bCon[4], jun_f.port_aSupIn) annotation(
    Line(points = {{-24, 6}, {-24, 260}, {-6, 260}, {-6, 288}}, color = {0, 127, 255}));
  connect(jun_f.port_bSupOut2, pipe_f_sub7.port_aDisSup) annotation(
    Line(points = {{-12, 294}, {-60, 294}}, color = {0, 127, 255}));
  connect(pipe_f_sub7.port_bDisRet, jun_f.port_aRetIn2) annotation(
    Line(points = {{-60, 306}, {-12, 306}}, color = {0, 127, 255}));
  connect(jun_f.port_bSupOut1, pipe_f_sub8.port_aDisSup) annotation(
    Line(points = {{12, 306}, {60, 306}}, color = {0, 127, 255}));
  connect(pipe_f_sub8.port_bDisRet, jun_f.port_aRetIn1) annotation(
    Line(points = {{60, 294}, {12, 294}}, color = {0, 127, 255}));
  connect(jun_f.port_bRetOut, dis.ports_aCon[4]) annotation(
    Line(points = {{6, 288}, {6, 260}, {24, 260}, {24, 6}}, color = {0, 127, 255}));

  // ---------------------------------------------------------------
  // Node h (con[5]) → sub9, sub10
  // ---------------------------------------------------------------
  connect(dis.ports_bCon[5], jun_h.port_aSupIn) annotation(
    Line(points = {{-24, 6}, {-24, 340}, {-6, 340}, {-6, 368}}, color = {0, 127, 255}));
  connect(jun_h.port_bSupOut2, pipe_h_sub9.port_aDisRet) annotation(
    Line(points = {{-12, 374}, {-60, 374}}, color = {0, 127, 255}));
  connect(pipe_h_sub9.port_bDisSup, jun_h.port_aRetIn2) annotation(
    Line(points = {{-60, 386}, {-12, 386}}, color = {0, 127, 255}));
  connect(jun_h.port_bSupOut1, pipe_h_sub10.port_aDisSup) annotation(
    Line(points = {{12, 386}, {60, 386}}, color = {0, 127, 255}));
  connect(pipe_h_sub10.port_bDisRet, jun_h.port_aRetIn1) annotation(
    Line(points = {{60, 374}, {12, 374}}, color = {0, 127, 255}));
  connect(jun_h.port_bRetOut, dis.ports_aCon[5]) annotation(
    Line(points = {{6, 368}, {6, 340}, {24, 340}, {24, 6}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // ETS substations
  // ---------------------------------------------------------------
  connect(pipe_a_sub1.port_bDisSup, ets[1].port_aSerHea) annotation(
    Line(points = {{-100, 54}, {-140, 54}, {-140, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[1].port_bSerHea, pipe_a_sub1.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 159.44}, {-160, 159.44}, {-160, 65.44}, {-100, 65.44}}, color = {0, 127, 255}));
  connect(pipe_a_sub2.port_bDisSup, ets[2].port_aSerHea) annotation(
    Line(points = {{100, 66}, {260, 66}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[2].port_bSerHea, pipe_a_sub2.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 53.44}, {100, 53.44}}, color = {0, 127, 255}));
  connect(pipe_b_sub3.port_bDisSup, ets[3].port_aSerHea) annotation(
    Line(points = {{-100, 134}, {-140, 134}, {-140, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[3].port_bSerHea, pipe_b_sub3.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 159.44}, {-160, 159.44}, {-160, 145.44}, {-100, 145.44}}, color = {0, 127, 255}));
  connect(pipe_b_sub4.port_bDisSup, ets[4].port_aSerHea) annotation(
    Line(points = {{100, 146}, {260, 146}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[4].port_bSerHea, pipe_b_sub4.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 133.44}, {100, 133.44}}, color = {0, 127, 255}));
  connect(pipe_d_sub5.port_bDisSup, ets[5].port_aSerHea) annotation(
    Line(points = {{-100, 214}, {-140, 214}, {-140, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[5].port_bSerHea, pipe_d_sub5.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 159.44}, {-160, 159.44}, {-160, 225.44}, {-100, 225.44}}, color = {0, 127, 255}));
  connect(pipe_d_sub6.port_bDisSup, ets[6].port_aSerHea) annotation(
    Line(points = {{100, 226}, {260, 226}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[6].port_bSerHea, pipe_d_sub6.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 213.44}, {100, 213.44}}, color = {0, 127, 255}));
  connect(pipe_f_sub7.port_bDisSup, ets[7].port_aSerHea) annotation(
    Line(points = {{-100, 294}, {-160, 294}, {-160, 252}, {260, 252}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[7].port_bSerHea, pipe_f_sub7.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 259.44}, {-140, 259.44}, {-140, 305.44}, {-100, 305.44}}, color = {0, 127, 255}));
  connect(pipe_f_sub8.port_bDisSup, ets[8].port_aSerHea) annotation(
    Line(points = {{100, 306}, {260, 306}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[8].port_bSerHea, pipe_f_sub8.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 293.44}, {100, 293.44}}, color = {0, 127, 255}));
  connect(pipe_h_sub9.port_bDisRet, ets[9].port_aSerHea) annotation(
    Line(points = {{-100, 374}, {-160, 374}, {-160, 350}, {260, 350}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[9].port_bSerHea, pipe_h_sub9.port_aDisSup) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 339.44}, {-140, 339.44}, {-140, 385.44}, {-100, 385.44}}, color = {0, 127, 255}));
  connect(pipe_h_sub10.port_bDisSup, ets[10].port_aSerHea) annotation(
    Line(points = {{100, 386}, {260, 386}, {260, 180}, {280, 180}}, color = {0, 127, 255}));
  connect(ets[10].port_bSerHea, pipe_h_sub10.port_aDisRet) annotation(
    Line(points = {{312, 179.44}, {340, 179.44}, {340, 374}, {100, 374}}, color = {0, 127, 255}));
// ---------------------------------------------------------------
// Close ring
// ---------------------------------------------------------------
  connect(dis.port_bDisSup, dis.port_aDisRet) annotation(
    Line(points = {{40, -14}, {80, -14}, {80, -26}, {40, -26}}, color = {0, 127, 255}));  


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
