from pathlib import Path
p=Path('../frontend/src/components/games/BoardGames.jsx');t=p.read_text(encoding='utf-8');a=t.index(' ช่อง');b=t.index('</p>',a);t=t[:a]+' petak'+t[b:];p.write_text(t,encoding='utf-8')
p=Path('../frontend/src/pages/GamesRoundPage.jsx');t=p.read_text(encoding='utf-8').replace('refreshUser','refreshMe');p.write_text(t,encoding='utf-8')
p=Path('../frontend/src/pages/VirtualTryOnPage.jsx');t=p.read_text(encoding='utf-8').replace('selected.discount_price ?? variant?.price ?? selected.price','variant?.price_override ?? selected.discount_price ?? selected.price');p.write_text(t,encoding='utf-8')
p=Path('../frontend/src/pages/CheckoutPage.jsx');t=p.read_text(encoding='utf-8');t=t.replace('  const [usePoints, setUsePoints] = useState(0);', '''  const [usePoints, setUsePoints] = useState(0);
  const [pointWallet, setPointWallet] = useState(null);
  const [cashbackEvents, setCashbackEvents] = useState([]);
  useEffect(() => {
    api.get('/points/logs').then(({ data }) => setPointWallet(data)).catch(() => {});
    api.get('/cashback-events').then(({ data }) => setCashbackEvents(data.events || [])).catch(() => {});
  }, []);''');t=t.replace('user.points_balance || 0','pointWallet?.balance ?? user.points_balance ?? 0');t=t.replace('(1 poin = Rp100)', '· rate mengikuti setiap perolehan');anchor='          {!!availableRewards.length';i=t.index(anchor);t=t[:i]+'''          {!!cashbackEvents.length && <p className="text-xs rounded-xl bg-teal-50 p-3">Event {cashbackEvents[0].name}: cashback {cashbackEvents[0].percent}% dalam bentuk poin setelah pesanan selesai. Poin berlaku {cashbackEvents[0].expiry_days} hari dan memakai rate yang dikunci pada pesanan.</p>}
'''+t[i:];p.write_text(t,encoding='utf-8')
