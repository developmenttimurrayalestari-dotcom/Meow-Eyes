import React, { useMemo, useRef, useState } from 'react';
import { shuffled, puzzleBoard } from '../../lib/gameEngine';
import { imageSrc } from '../../lib/api';
const FACES = ['🐱', '🐟', '🐾', '👓', '🚀', '⭐', '🌙', '🧶'];
export function MatchingGame({ round, onFinish }) {
  const deck = useMemo(() => shuffled(round.seed, [...Array(8).keys(), ...Array(8).keys()]), [round.seed]);
  const [matched, setMatched] = useState([]), [open, setOpen] = useState([]), locked = useRef(false), moves = useRef([]);
  const choose = i => {
    if (locked.current || matched.includes(i) || open.includes(i)) return;
    moves.current.push(i); const next = [...open, i]; setOpen(next);
    if (next.length === 2) {
      locked.current = true;
      if (deck[next[0]] === deck[next[1]]) {
        const found = [...matched, ...next]; setMatched(found); setOpen([]); locked.current = false;
        if (found.length === 16) { locked.current = true; onFinish({ moves: moves.current }); }
      } else setTimeout(() => { setOpen([]); locked.current = false; }, 700);
    }
  };
  return <div className="max-w-lg mx-auto"><p className="mb-3 text-sm">Temukan 8 pasangan kartu. Pasangan: {matched.length / 2} / 8</p><div className="grid grid-cols-4 gap-3">{deck.map((face, i) => <button key={i} type="button" disabled={matched.includes(i)} onClick={() => choose(i)} aria-label={`Kartu ${i + 1}${open.includes(i) || matched.includes(i) ? ': ' + FACES[face] : ''}`} className={`aspect-square rounded-2xl text-3xl ${matched.includes(i) ? 'bg-teal-100' : 'bg-meow-bg border-2 border-meow-salmon/20'}`}>{open.includes(i) || matched.includes(i) ? FACES[face] : '?'}</button>)}</div></div>;
}
export function SlidePuzzle({ round, onFinish }) {
  const level = round.snapshot.level, [board, setBoard] = useState(() => puzzleBoard(round.seed, level.rows, level.columns)), moves = useRef([]), done = useRef(false);
  const move = index => {
    const empty = board.indexOf(0);
    if (done.current || Math.abs(Math.floor(index / level.columns) - Math.floor(empty / level.columns)) + Math.abs(index % level.columns - empty % level.columns) !== 1) return;
    const next = [...board]; [next[empty], next[index]] = [next[index], next[empty]]; moves.current.push(index); setBoard(next);
    if (next.every((v, i) => v === (i + 1) % next.length)) { done.current = true; onFinish({ moves: moves.current }); }
  };
  return <div className="max-w-xl mx-auto"><p className="mb-3 text-sm">Level {level.level} · {level.rows} × {level.columns} petak</p><p className="text-sm mb-3">Geser petak di samping ruang kosong hingga gambar kembali utuh. Langkah: {moves.current.length}</p><div className="grid gap-1 rounded-xl overflow-hidden bg-meow-midnight/10" style={{ gridTemplateColumns: `repeat(${level.columns}, 1fr)` }}>{board.map((value, index) => <button type="button" key={index} onClick={() => move(index)} aria-label={value ? `Geser petak ${value}` : 'Ruang kosong'} disabled={!value} className="aspect-square relative overflow-hidden" style={value ? { backgroundImage: `url("${imageSrc(level.image_url)}")`, backgroundSize: `${level.columns * 100}% ${level.rows * 100}%`, backgroundPosition: `${((value - 1) % level.columns) / (level.columns - 1) * 100}% ${Math.floor((value - 1) / level.columns) / (level.rows - 1) * 100}%` } : {}}>{value > 0 && <span className="absolute bottom-0 right-0 rounded-tl bg-black/60 text-white text-xs px-1.5">{value}</span>}</button>)}</div><details className="mt-3 text-sm"><summary>Lihat gambar utuh</summary><img src={imageSrc(level.image_url)} alt="Contoh gambar puzzle lengkap" className="mt-2 max-h-48 rounded-xl" /></details></div>;
}
