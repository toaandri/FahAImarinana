import fs from 'node:fs/promises';
import {FileBlob,Presentation,PresentationFile} from 'file:///C:/Users/Pricio/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=await PresentationFile.importPptx(await FileBlob.load('C:/Users/Pricio/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-review/assets/reference.pptx'));
console.log('SHAPES',Object.getOwnPropertyNames(Object.getPrototypeOf(p.slides.items[0].shapes)));console.log('SHAPE',Object.getOwnPropertyNames(Object.getPrototypeOf(p.slides.items[0].shapes.items[0]))); console.log(Object.getOwnPropertyNames(Object.getPrototypeOf(p.slides)));
await fs.writeFile('C:/FahAImarinana/.slides-build/template-inspect.json',JSON.stringify(p.toSnapshot()));
for(let i=0;i<p.slides.items.length;i++){let s=p.slides.items[i]; if(i===0||i===7){let b=await s.export({format:'png',scale:.7});await fs.writeFile('C:/FahAImarinana/.slides-build/template-'+i+'.png',new Uint8Array(await b.arrayBuffer()));}}



