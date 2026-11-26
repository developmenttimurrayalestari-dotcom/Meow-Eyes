// Used only when navigation cannot be loaded, never for a configured empty menu.
const header = [
  ['nav-home','Beranda','/','none'], ['nav-shop-now','Shop Now','/shop-now','none'],
  ['nav-new-arrival','New Arrival','/new-arrival','none'], ['nav-meowsurement','Meowsurement','/meowsurement/','none'],
  ['nav-virtual-try-on','Virtual Try-On','/virtual-try-on','none'], ['nav-our-product','Our Product','/our-product','none'],
  ['nav-articles','Article','/articles','none'], ['nav-flashsale','Flash Sale','/flash-sale','flash'],
  ['nav-games','Games','/games','games'], ['nav-contact','Contact','/contact','none'],
];
const footer = [
  ['footer-shop','Shop Now','/shop-now','none'], ['footer-new','New Arrival','/new-arrival','none'],
  ['footer-meowsurement','Meowsurement','/meowsurement/','none'], ['footer-frame','Frame New Arrival','/new-arrival?product_type=frame','none'],
  ['footer-flash','Flash Sale','/flash-sale','none'], ['footer-products','Our Product','/our-product','none'],
  ['footer-articles','Article','/articles','none'], ['footer-games','Mini Games','/games','none'],
  ['footer-vto','Virtual Try-On','/virtual-try-on','none'], ['footer-roulette','Roulette Reward','/roulette','none'],
];
const mobile = [['bn-home','Home','/','home'],['bn-shop','Shop','/shop-now','shop'],['bn-games','Games','/games','games'],['bn-cart','Cart','/cart','cart'],['bn-profile','Profil','/profile','profile']];
export const DEFAULT_MENUS = [['header',header],['footer',footer],['mobile',mobile]].flatMap(([location, items]) => items.map(([id,label,url,icon],sort_order)=>({id,label,url,icon,location,sort_order,is_active:true,new_tab:false})));
