const config={...require('./package.json').build};
// Public CI can build the openly licensed baseline without restricted research assets.
if(process.env.IMI_BASELINE_ONLY==='1'){
  config.extraResources=[];
  config.artifactName='Imi-baseline-${version}-${arch}.${ext}';
}
module.exports=config;
