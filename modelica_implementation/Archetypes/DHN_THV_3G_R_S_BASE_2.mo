within modelica_implementation.Archetypes;

model DHN_THV_3G_R_S_BASE_2
   "Benchmark network DHN_THV_3G_R_S_BASE
   Thermo-Hydraulic Validation — 3rd Generation District Heating — Radial — Small.
   N=15 nodes (1 source, 4 junctions, 10 substations).
   E=14 pipe segments (4 trunk DN50/DN65 + 10 branch DN25).
   L=0 independent loops (radial tree topology).
   Simulation: 7 days, 10-min resolution (1008 timesteps).
   Control: VF-CT (variable flow, constant temperature), T_sup=80 degC.
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
    "Number of ETS connection nodes on the network";
 
  parameter Integer nCon_h = 5
    "Number of ETS connection nodes on horizontal trunk";
    
  parameter Integer nCon_v = 5
    "Number of ETS connection nodes on vertical trunk";
    
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
    Placement(transformation(origin = {-160, 0}, extent = {{-20,-20},{20,20}})));
  
  // ---------------------------------------------------------------
  // ETS substations (10 instances)
  // ---------------------------------------------------------------
  BuildingWithIndirectETS ets_v[nCon_v](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam             = filNam,
    each facMul             = 1.0,
    each TDisSup_nominal    = TDisSupSet,
    each THeaWatSup_nominal = THeaWatSup_nominal,
    each THeaWatRet_nominal = THeaWatRet_nominal,
    each dTDis_nominal      = dTDis_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {136, 4}, extent = {{-16,-16},{16,16}})));
  
  BuildingWithIndirectETS ets_h[nCon_h](
    redeclare each package MediumSer = Medium,
    redeclare each package MediumBui = Medium,
    each filNam             = filNam,
    each facMul             = 1.0,
    each TDisSup_nominal    = TDisSupSet,
    each THeaWatSup_nominal = THeaWatSup_nominal,
    each THeaWatRet_nominal = THeaWatRet_nominal,
    each dTDis_nominal      = dTDis_nominal)
    "ETS substations 1..10" annotation(
    Placement(transformation(origin = {136, 54}, extent = {{-16,-16},{16,16}})));

  // ---------------------------------------------------------------
  // Derived nominal flow rates
  // ---------------------------------------------------------------
  parameter Modelica.Units.SI.MassFlowRate mDis_flow_nominal =
    m_sub * nCon / 2 * 1.20
    "Nominal mass flow rate leaving the plant [kg/s]";
     
  parameter Modelica.Units.SI.MassFlowRate mCon_flow_nominal[nCon_v] =
    ets_v.mDis_flow_nominal * 1.05
    "Nominal mass flow rate at each ETS branch [kg/s]";
  
  // ---------------------------------------------------------------
  // Trunk src -> b -> d
  // ---------------------------------------------------------------
  Buildings.DHC.Networks.Distribution2PipePlugFlow_v dis_bd(
    redeclare package Medium = Medium,
    nCon                  = nCon_h,
    mDis_flow_nominal     = mDis_flow_nominal,
    mCon_flow_nominal     = mCon_flow_nominal,
    mEnd_flow_nominal     = m_sub,
    mDisCon_flow_nominal = {mDis_flow_nominal - i*m_sub*1.05 for i in 0:(nCon_h-1)},
    lDis = {102.5, 0.1, 122.3, 0.1, 0.1},
    lEnd                  = 1,
    v_nominal             = 1.77,
    dIns                  = 0.03195,
    kIns                  = 0.033,
    allowFlowReversal     = true,
    iConDpSen             = nCon_h,
    roughness             = 4.5e-5,
    thickness             = 0.03195, 
    show_entFlo = true)
    "Horizontal trunk" annotation(
    Placement(transformation(origin = {0, 6}, extent = {{-40,-20},{40,20}})));
 
  // ---------------------------------------------------------------
  // Trunk src -> a -> c
  // ---------------------------------------------------------------
  Buildings.DHC.Networks.Distribution2PipePlugFlow_v dis_ac(
    redeclare package Medium = Medium,
    nCon                  = nCon_v,
    mDis_flow_nominal     = mDis_flow_nominal,
    mCon_flow_nominal     = mCon_flow_nominal,
    mEnd_flow_nominal     = m_sub,
    mDisCon_flow_nominal = {mDis_flow_nominal - i*m_sub*1.05 for i in 0:(nCon_v-1)},
    lDis = {163.9, 0.1, 127.5, 0.1, 0.1},
    lEnd                  = 1,
    v_nominal             = 1.77,
    dIns                  = 0.03195,
    kIns                  = 0.033,
    allowFlowReversal     = true,
    iConDpSen             = nCon_v,
    roughness             = 4.5e-5,
    thickness             = 0.03195, 
    show_entFlo = true)
    "Vertical trunk" annotation(
    Placement(transformation(origin = {-94, -80}, extent = {{-40,-20},{40,20}}, rotation = -90)));
 
  // ---------------------------------------------------------------
  // Ground temperature
  // ---------------------------------------------------------------
  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroDis_h[nCon_h + 1](
    each T = TGround)
    "Ground temperature for supply horizontal trunk" annotation(
    Placement(transformation(origin = {-150, 100}, extent = {{-10,-10},{10,10}})));

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroRet_h[nCon_h](
    each T = TGround)
    "Ground temperature for return horizontal trunk" annotation(
    Placement(transformation(origin = {-150, 60}, extent = {{-10,-10},{10,10}})));
  
    Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroDis_v[nCon_v + 1](
    each T = TGround)
    "Ground temperature for supply vertical trunk" annotation(
    Placement(transformation(origin = {-170, -130}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TGroRet_v[nCon_v](
    each T = TGround)
    "Ground temperature for return vertical trunk" annotation(
    Placement(transformation(origin = {-170, -90}, extent = {{-10, -10}, {10, 10}})));

  // ---------------------------------------------------------------
  // Branch pipes to substations (10 segments, all DN25)
  // ---------------------------------------------------------------
    DHNPipe pipe_sub_h[nCon_h](
    redeclare each package Medium = Medium,
    length = {173.6, 167.7, 142.2, 103.0, 121.9},
    each d_inner        = 0.0282,
    each dIns           = 0.02815,
    each kIns           = 0.033,
    each roughness      = 4.5e-5,
    m_flow_nominal      = ets_h.mDis_flow_nominal,
    each TGround        = TGround)
    "Branch pipes sub1, sub2, sub5, sub 6, sub7 — DN25" annotation(
    Placement(transformation(origin = {0, 80}, extent = {{-20,-20},{20,20}}, rotation = 90)));
    
    DHNPipe pipe_sub_v[nCon_v](
    redeclare each package Medium = Medium,
    length = {189.2, 108.7, 150.5, 102.7, 119.9},
    each d_inner        = 0.0282,
    each dIns           = 0.02815,
    each kIns           = 0.033,
    each roughness      = 4.5e-5,
    m_flow_nominal      = ets_v.mDis_flow_nominal,
    each TGround        = TGround)
    "Branch pipes sub3, sub4, sub8, sub 9, sub10 — DN25" annotation(
    Placement(transformation(origin = {20, -78}, extent = {{-20,-20},{20,20}})));
 
  // ---------------------------------------------------------------
  // Source junction
  // ---------------------------------------------------------------
  DHNJunction jun_src(
    redeclare package Medium = Medium,
    m_flow_nominal = m_total)
    "Source junction: splits total flow toward trunk a and trunk b" annotation(
    Placement(transformation(origin = {-100, 0}, extent = {{-20, -20}, {20, 20}})));

equation
  
  // ---------------------------------------------------------------
  // Distribution connections
  // ---------------------------------------------------------------
  connect(src.port_bDis, jun_src.port_aSupIn) annotation(
    Line(points = {{-140, 4}, {-112, 4}, {-112, 6}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut1, dis_bd.port_aDisSup) annotation(
    Line(points = {{-88, 6}, {-40, 6}}, color = {0, 127, 255}));
  connect(dis_bd.port_bDisRet, jun_src.port_aRetIn1) annotation(
    Line(points = {{-40, -6}, {-88, -6}}, color = {0, 127, 255}));
  connect(jun_src.port_bRetOut, src.port_aDis) annotation(
    Line(points = {{-112, -6}, {-140, -6}, {-140, -4}}, color = {0, 127, 255}));
  connect(jun_src.port_bSupOut2, dis_ac.port_aDisSup) annotation(
    Line(points = {{-94, -12}, {-94, -40}}, color = {0, 127, 255}));
  connect(jun_src.port_aRetIn2, dis_ac.port_bDisRet) annotation(
    Line(points = {{-106, -12}, {-106, -40}}, color = {0, 127, 255}));
  
  // ---------------------------------------------------------------
  // Heat ports connection
  // ---------------------------------------------------------------
  connect(TGroDis_h.port, dis_bd.heatPortsDis) annotation(
    Line(points = {{-140, 100}, {-60, 100}, {-60, 18}, {16, 18}, {16, 10}}, color = {191, 0, 0}, thickness = 0.5));
  connect(TGroRet_h.port, dis_bd.heatPortsRet) annotation(
    Line(points = {{-140, 60}, {-52, 60}, {-52, -20}, {-14, -20}, {-14, -10}}, color = {191, 0, 0}, thickness = 0.5));
  connect(TGroRet_v.port, dis_ac.heatPortsRet) annotation(
    Line(points = {{-160, -90}, {-140, -90}, {-140, -66}, {-110, -66}}, color = {191, 0, 0}, thickness = 0.5));
  connect(TGroDis_v.port, dis_ac.heatPortsDis) annotation(
    Line(points = {{-160, -130}, {-60, -130}, {-60, -80}, {-84, -80}, {-84, -96}, {-90, -96}}, color = {191, 0, 0}, thickness = 0.5));
  
  // ---------------------------------------------------------------
  // Pipe connections
  // ---------------------------------------------------------------
  connect(dis_bd.ports_bCon, pipe_sub_h.port_aDisSup) annotation(
    Line(points = {{-24, 26}, {-24, 48}, {-6, 48}, {-6, 60}}, color = {0, 127, 255}, thickness = 0.5));
  connect(pipe_sub_h.port_bDisRet, dis_bd.ports_aCon) annotation(
    Line(points = {{6, 60}, {6, 48}, {24, 48}, {24, 26}}, color = {0, 127, 255}, thickness = 0.5));
  connect(dis_ac.ports_bCon, pipe_sub_v.port_aDisSup) annotation(
    Line(points = {{-74, -56}, {-20, -56}, {-20, -72}, {0, -72}}, color = {0, 127, 255}, thickness = 0.5));
  connect(pipe_sub_v.port_bDisRet, dis_ac.ports_aCon) annotation(
    Line(points = {{0, -84}, {-20, -84}, {-20, -104}, {-74, -104}}, color = {0, 127, 255}, thickness = 0.5));
// ---------------------------------------------------------------
// Substation connections
// ---------------------------------------------------------------
  connect(pipe_sub_h.port_bDisSup, ets_h.port_aSerHea) annotation(
    Line(points = {{-6, 100}, {-6, 120}, {100, 120}, {100, 52}, {120, 52}}, color = {0, 127, 255}, thickness = 0.5));
  connect(ets_h.port_bSerHea, pipe_sub_h.port_aDisRet) annotation(
    Line(points = {{152, 52}, {180, 52}, {180, 110}, {6, 110}, {6, 100}}, color = {0, 127, 255}, thickness = 0.5));
  connect(pipe_sub_v.port_bDisSup, ets_v.port_aSerHea) annotation(
    Line(points = {{40, -72}, {100, -72}, {100, 2}, {120, 2}}, color = {0, 127, 255}, thickness = 0.5));
  connect(ets_v.port_bSerHea, pipe_sub_v.port_aDisRet) annotation(
    Line(points = {{152, 2}, {180, 2}, {180, -84}, {40, -84}}, color = {0, 127, 255}, thickness = 0.5));  

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
end DHN_THV_3G_R_S_BASE_2;
