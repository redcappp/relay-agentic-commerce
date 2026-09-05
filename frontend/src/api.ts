export const API=import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const money=(value:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(value);
export async function api(path:string, body?:unknown) {
  const response=await fetch(API+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  const data=await response.json(); if(!response.ok) throw new Error(data.detail || 'Request failed'); return data;
}
