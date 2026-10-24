'use strict';
// Official frozen source. Extract with Python zipfile into research/emsr417.
const fs=require('node:fs'),crypto=require('node:crypto');
(async()=>{
 const url='https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR417/EMSR417_AOI01_DEL_PRODUCT_r1_RTP01_v1_vector.zip';
 const r=await fetch(url);if(!r.ok)throw Error('Official source HTTP '+r.status);
 const b=Buffer.from(await r.arrayBuffer());const sha=crypto.createHash('sha256').update(b).digest('hex');
 if(sha!=='94001db0ca60c8052ec7eac79d1d97985b651c9650ee4047bb0eaabe0a0f87cc')throw Error('Source changed; review provenance before reanalysis');
 fs.mkdirSync('research',{recursive:true});fs.writeFileSync('research/emsr417-vector.zip',b);console.log('EMSR417 source verified',sha);
})().catch(e=>{console.error(e.message);process.exitCode=1});
