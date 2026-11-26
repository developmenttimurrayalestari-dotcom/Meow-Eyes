import React,{useEffect,useState} from 'react';
import { Icon,Glasses,Layers,Package2,Sparkles,Tag,Home,Gamepad2,ShoppingCart,User,BookOpen,Zap,Mail,CircleHelp } from 'lucide-react';
import { iconName,loadIconCatalog } from '../lib/iconLibrary';
const legacy={frame:Glasses,lens:Layers,package:Package2,sparkles:Sparkles,tag:Tag,glasses:Glasses,home:Home,shop:Sparkles,games:Gamepad2,cart:ShoppingCart,profile:User,article:BookOpen,flash:Zap,contact:Mail};
export default function AppIcon({name,...props}) {
  const [loaded,setLoaded]=useState(null);
  const Legacy=Object.prototype.hasOwnProperty.call(legacy,name)?legacy[name]:null;
  useEffect(()=>{
    if(!name||name==='none'||Legacy)return;
    let active=true;
    loadIconCatalog().then(catalog=>{const node=catalog.icons[iconName(name)];if(active)setLoaded({name,node:Array.isArray(node)?node:null});}).catch(()=>{});
    return()=>{active=false;};
  },[name,Legacy]);
  if(!name||name==='none')return null;
  if(Legacy)return <Legacy aria-hidden="true" {...props}/>;
  if(loaded?.name===name&&loaded.node)return <Icon iconNode={loaded.node} aria-hidden="true" {...props}/>;
  return <CircleHelp aria-hidden="true" {...props}/>;
}
