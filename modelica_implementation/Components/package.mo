within modelica_implementation;
package Components
  "Reusable custom blocks for assembling DHN benchmark networks.
   All components use Buildings.Media.Water as default medium and follow
   a consistent port-naming convention (port_aDisSup/port_bDisSup for supply,
   port_aDisRet/port_bDisRet for return) to allow direct interconnection.
  "

  annotation(
    Documentation(info = "<html>
<p>
This package contains the building blocks shared by all benchmark archetypes:
</p>
<ul>
<li><b>PlantStation</b> — central heat plant (pump, ideal heater, expansion vessel)</li>
<li><b>DHNPipe</b> — instrumented two-pipe segment (supply + return, plug-flow, ground losses)</li>
<li><b>DHNJunction</b> — instrumented two-pipe T-junction for radial tree networks</li>
<li><b>BuildingWithIndirectETS</b> — substation with indirect ETS and time-series heating load</li>
</ul>
</html>"));
end Components;
