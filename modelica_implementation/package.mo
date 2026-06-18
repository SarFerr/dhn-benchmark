package DHN_Benchmark
  "Benchmark networks for district heating systems.
   Companion library to the paper:
   'Synthetic Benchmark Networks for District Heating Systems:
   A Comprehensive Review and Standardisation Framework'
   (Ferrero, Schiera, Minuto, Lanzini).

   Structure:
     Components — reusable custom block
     Archetypes — concrete benchmark networks

   Requires: Modelica Standard Library 4.1.0, Buildings Library 13.0.0
  "

  annotation(
    uses(Buildings(version = "13.0.0"), Modelica(version = "4.1.0")),
    Documentation(info = "<html>
<p>
This library provides a reproducible set of synthetic benchmark district
heating networks (DHNs) for thermo-hydraulic solver validation, modelled
in OpenModelica using the Buildings.DHC framework.
</p>
<h5>Components</h5>
<ul>
<li><code>PlantStation</code> — ideal central heat plant (pump + heater + expansion vessel)</li>
<li><code>DHNPipe</code> — two-pipe segment with plug-flow thermal transport and ground heat loss</li>
<li><code>DHNJunction</code> — two-pipe T-junction for radial tree topologies</li>
<li><code>BuildingWithIndirectETS</code> — substation with indirect heat exchanger and time-series load</li>
</ul>
<h5>Archetypes</h5>
<ul>
<li><code>DHN_THV_3G_R_S_BASE</code> — Thermo-Hydraulic Validation, 3GDH, Radial, Small (baseline)</li>
</ul>
</html>"));
end DHN_Benchmark;
