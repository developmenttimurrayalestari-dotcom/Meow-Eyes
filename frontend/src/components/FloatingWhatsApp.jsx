import React, { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { useLocation } from "react-router-dom";
import { api } from "../lib/api";

export default function FloatingWhatsApp() {
  const { pathname } = useLocation();
  const isAdmin = /^\/admin(?:\/|$)/i.test(pathname);
  const [settings, setSettings] = useState(null);
  useEffect(() => {
    if (isAdmin) return;
    let active = true;
    const load = () => api.get("/settings/whatsapp").then(({ data }) => { if (active) setSettings(data); }).catch(() => {});
    load();
    window.addEventListener("focus", load);
    window.addEventListener("meow:whatsapp-updated", load);
    return () => {
      active = false;
      window.removeEventListener("focus", load);
      window.removeEventListener("meow:whatsapp-updated", load);
    };
  }, [isAdmin]);
  const phone = String(settings?.phone_number || "").replace(/\D/g, "");
  if (isAdmin || !settings?.enabled || !/^[1-9]\d{6,14}$/.test(phone)) return null;
  const href = `https://wa.me/${phone}?text=${encodeURIComponent(settings.default_text || "")}`;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" aria-label="Hubungi toko melalui WhatsApp" title="Chat WhatsApp"
      className="fixed right-4 bottom-24 md:right-6 md:bottom-6 z-40 flex items-center gap-2 rounded-full bg-green-600 hover:bg-green-700 text-white p-4 shadow-xl focus-visible:outline focus-visible:outline-4 focus-visible:outline-green-300"
      data-testid="floating-whatsapp">
      <MessageCircle className="h-6 w-6" aria-hidden="true" />
      <span className="hidden sm:inline font-bold text-sm">Chat WhatsApp</span>
    </a>
  );
}
