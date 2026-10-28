'use strict';
// Original geometric app icon, rendered without external assets or services.
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const size=256;
function crc32(buffer){let crc=0xffffffff;for(const b of buffer){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
function chunk(type,data){const name=Buffer.from(type),length=Buffer.alloc(4),crc=Buffer.alloc(4);length.writeUInt32BE(data.length);crc.writeUInt32BE(crc32(Buffer.concat([name,data])));return Buffer.concat([length,name,data,crc]);}
function inside(x,y){const dx=Math.max(36-x,0,x-220),dy=Math.max(36-y,0,y-220);return dx*dx+dy*dy<=36*36;}
function color(x,y){if(!inside(x,y))return[0,0,0,0];const pale=[193,220,183,255],white=[244,246,233,255];if(x>=60&&x<91&&y>=62&&y<94)return pale;if(x>=60&&x<91&&y>=113&&y<194)return white;if(x>=116&&x<194&&y>=62&&y<84)return pale;if(x>=116&&x<175&&y>=112&&y<134)return white;if(x>=116&&x<194&&y>=172&&y<194)return pale;return[23,70,60,255];}
const raw=Buffer.alloc(size*(1+size*4));
for(let y=0;y<size;y++)for(let x=0;x<size;x++){const average=[0,0,0,0];for(const dx of [.25,.75])for(const dy of [.25,.75])color(x+dx,y+dy).forEach((v,i)=>average[i]+=v/4);average.forEach((v,i)=>raw[y*(1+size*4)+1+x*4+i]=Math.round(v));}
const header=Buffer.alloc(13);header.writeUInt32BE(size);header.writeUInt32BE(size,4);header[8]=8;header[9]=6;
const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);
const ico=Buffer.alloc(22);ico.writeUInt16LE(1,2);ico.writeUInt16LE(1,4);ico.writeUInt16LE(1,10);ico.writeUInt16LE(32,12);ico.writeUInt32LE(png.length,14);ico.writeUInt32LE(22,18);
const destination=path.join(__dirname,'../src/assets');fs.mkdirSync(destination,{recursive:true});fs.writeFileSync(path.join(destination,'icon.png'),png);fs.writeFileSync(path.join(destination,'icon.ico'),Buffer.concat([ico,png]));
