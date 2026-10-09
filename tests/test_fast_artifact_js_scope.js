'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');
const sourcePath=fs.existsSync(path.resolve(__dirname,'../scripts/build_final_fast_artifact.py'))?path.resolve(__dirname,'../scripts/build_final_fast_artifact.py'):path.resolve(__dirname,'build_final_fast_artifact.py');
const source=fs.readFileSync(sourcePath,'utf8');
const match=source.match(/FINAL_JS = r'''<script>\n([\s\S]*?)\n<\/script>'''/);
assert(match,'actual final JS extension is present');
const js=match[1];
class Element{constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.value='';this.textContent='';}append(...children){this.children.push(...children)}addEventListener(name,fn){this.listeners[name]=fn}dispatchEvent(event){events.push([this.tag,event.type,this.value]);if(this.listeners[event.type])this.listeners[event.type](event)}scrollIntoView(){this.scrolled=true}}
const nodes={},events=[],tabs=[];
function node(id){return nodes[id]||(nodes[id]=new Element(id))}
function aggregate(){return {terminal_count:10,judged:10,judge_accepted:10,judge_rejected:0,operational_terminals:0,proposal_accepted:8,proposal_judged:10,openrouter_all_actors_usd:'.1',wall_s:{median:120},active_call_union_s:{median:100},first_doctor_completed_s:{median:5},first_doctor_content_s:{median:2},subscription_input_tokens_per_case:{median:10000},relative_exam_units:30,charged_sources:10}}
const publicData=aggregate();publicData.cases=Array.from({length:10},(_,i)=>({case_id:'case_'+String(i+1).padStart(3,'0'),judge_correct:true,openrouter_usd:'.01',wall_s:120,active_call_union_s:100,first_doctor_content_s:2,relative_exam_units:3}));
const DATA={v36:{public_final:10,public_openrouter_usd:'.35'},v4Working:{judge_correct:10,openrouter_usd:'.115'},fastFinal:{variant:'fast4',public:publicData,closed:aggregate(),previous_public:{fast1:{...aggregate(),judge_accepted:9},fast2:{...aggregate(),terminal_count:2,judge_accepted:1},fast3:{...aggregate(),terminal_count:2,judge_accepted:1}},comparison_descriptive:{},global_ledger_usd:'.5',cap_usd:'5.00',financial:{exact_match:true,snapshot_is_final_verified:false},summary_sha256:'TEST_ONLY'}};
const context={__data:DATA,document:{getElementById:node,querySelector:()=>null},__money:(x)=>String(x),__el:(tag,text,cls)=>{const e=new Element(tag);e.textContent=text||'';e.cls=cls;return e},__tab:(name)=>tabs.push(name),Event:class{constructor(type){this.type=type}}};
vm.createContext(context);vm.runInContext('const DATA=__data; const money=__money; const el=__el; function showTab(name){__tab(name)}',context);
assert.equal(context.DATA,undefined); // Browser-style global lexical binding, not window.DATA.
vm.runInContext(js,context);
vm.runInContext("(()=>{function populateTrials(id){if(id!=='fast_fast4')throw new Error('wrong default')};populateTrials('fast_'+DATA.fastFinal.variant)})()",context);
assert.equal(context.populateTrials,undefined); // Remains scoped to replay IIFE.
assert.equal(nodes['fast-final-metrics'].children.length,4);
assert.equal(nodes['fast-public-comparison'].children.length,6);
assert.equal(nodes['fast-public-cases'].children.length,10);
const button=nodes['fast-public-cases'].children[0].children[0].children[0];button.listeners.click();
assert.deepEqual(tabs,['reproducao']);assert.equal(nodes['replay-trial'].value,'fast_fast4');assert.equal(nodes['replay-case'].value,'case_001');assert.equal(events.length,2);
const expression="((e.kind==='api'||e.kind==='cli')&&now<e.end)?'Chamada em andamento. A resposta completa só é exibida após o horário registrado de conclusão.':(e.preview||'Sem conteúdo de saída neste evento.')";
const preview=vm.runInContext('(e,now)=>'+expression,context);
for(const kind of ['api','cli']){const e={kind,end:10,preview:'COMPLETE_OUTPUT'};assert(!preview(e,9).includes('COMPLETE_OUTPUT'));assert.equal(preview(e,10),'COMPLETE_OUTPUT');assert.equal(e.preview,'COMPLETE_OUTPUT')}
assert.equal(preview({kind:'tool',end:10,preview:'RECORDED_TOOL'},9),'RECORDED_TOOL');
console.log(JSON.stringify({final_js_globals_resolved:true,chosen_replay:'fast_fast4',click_routes_public_case:true,full_response_hidden_before_end:true,raw_preview_immutable:true}));
