within modelica_implementation;
package Archetypes
  "Concrete synthetic benchmark district heating networks.
   Each archetype is identified by a six-field code:
   DHN_{Objective}_{Generation}_{Topology}_{Scale}_{Variant}, e.g.
   DHN_THV_3G_R_S_BASE (Thermo-Hydraulic Validation, 3GDH, Radial, Small, base scenario).
  "

  annotation(
    Documentation(info = "<html>
<p>
Benchmark networks organised in three validation classes, as defined in
Section 6 of the companion paper:
</p>
<ul>
<li><b>THV</b> — Thermo-Hydraulic Validation (radial / ring / meshed, 3GDH, small)</li>
<li><b>TG</b> — Technology assessment (3GDH / 4GDH / 5GDHC, medium scale)</li>
<li><b>CS</b> — Computational scalability (3GDH meshed, small / medium / large)</li>
</ul>
<p>
Currently implemented: <code>DHN_THV_3G_R_S_BASE</code> (radial baseline).
</p>
</html>"));
end Archetypes;
