import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, setToken } from "../lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cartCount, setCartCount] = useState(0);

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data.user);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshCartCount = useCallback(async () => {
    try {
      const { data } = await api.get("/cart");
      setCartCount(data.count || 0);
    } catch {
      setCartCount(0);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  useEffect(() => {
    if (user) refreshCartCount();
    else setCartCount(0);
  }, [user, refreshCartCount]);

  useEffect(() => {
    const h = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener("meow:unauthorized", h);
    return () => window.removeEventListener("meow:unauthorized", h);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.token) setToken(data.token);
    setUser(data.user);
    return data.user;
  };
  const register = async (payload) => {
    const { data } = await api.post("/auth/register", payload);
    if (data.token) setToken(data.token);
    setUser(data.user);
    return data.user;
  };
  const loginWithGoogle = async (credential, nonce) => {
    const { data } = await api.post("/auth/google", { credential, nonce });
    if (data.token) setToken(data.token);
    setUser(data.user);
    return data.user;
  };
  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore
    }
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, setUser, loading, login, register, loginWithGoogle, logout, refreshMe: fetchMe, cartCount, refreshCartCount }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
