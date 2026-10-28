const test=require('node:test'),assert=require('node:assert/strict');
const {parsePairs}=require('../src/files.cjs');
test('CSV imports quoted commas, embedded newlines and BOM headers',()=>{
  assert.deepEqual(parsePairs('\uFEFFjapanese,english\r\n"彼は来ない。","He will not come,\nhe said."','.csv'),[{japanese:'彼は来ない。',english:'He will not come,\nhe said.'}]);
});
test('CSV requires both columns and closed quotes',()=>{assert.throws(()=>parsePairs('source,target\na,b','.csv'));assert.throws(()=>parsePairs('japanese,english\n"abc,def','.csv'));});
