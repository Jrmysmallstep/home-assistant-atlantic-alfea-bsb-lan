"use strict";
const assert=require("assert");
const fs=require("fs"),vm=require("vm"),path=require("path");
const filename=path.join(__dirname,"..","custom_components","atlantic_alfea_controller","www","pac-synoptique-card.js");
const src=fs.readFileSync(filename,"utf8");
// V1.5.13 regression: CSS ':host(portrait) .inlink, .outlink{height:38px}'
// applied its unprefixed second selector to EVERY .outlink, including landscape.
for (const mode of ["portrait","auto"]){
  const prefix=`:host([data-orientation="${mode}"])`;
  const pair=[
    [".machine",".pac"],
    [".inlink",".outlink"],
    [".output-card.heat:after",".output-card.cool:after"]
  ];
  for(const [left,right] of pair){
    const bad=`${prefix} ${left}, ${right}{`;
    assert(!src.includes(bad), `Unscoped global CSS in ${mode}: ${bad}`);
    const good=`${prefix} ${left}, ${prefix} ${right}{`;
    assert(src.includes(good),`Missing scoped CSS rule in ${mode}: ${good}`);
  }
}
assert(src.includes('.outlink{grid-column:4;grid-row:1/4;align-self:stretch}'),
  "Landscape connector must span all 3 rows");
assert(src.includes("M0 220H33V72H100 M33 220H100 M33 220V368H100"),
  "3-way hydraulic sketch removed");
assert(src.includes("data-orientation=\"landscape\""),"Landscape mode missing");
const keys=src.match(/const FIELDS = \{([\s\S]*?)\n\};/);
assert(keys,"FIELDS map missing");
assert((keys[1].match(/^\s+[A-Za-z_][\w]*\s*:/gm)||[]).length>=65);
assert(!src.includes("this._hass.callService('select'") && !src.includes("this._hass.callService('number'"),"PAC write in card");
assert(!/<img\b/i.test(src),"Images must remain inlined CSS/SVG");
console.log("PASS: landscape hydraulic connectors remain full-height and CSS scope is isolated");
