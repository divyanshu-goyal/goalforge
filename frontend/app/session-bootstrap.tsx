"use client";

import { useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SessionBootstrap() {
  useEffect(() => {
    if (window.sessionStorage.getItem("goalforge_session_initialized")) return;

    window.sessionStorage.setItem("goalforge_session_initialized", "true");
    fetch(`${API_URL}/api/session`, { credentials: "include" }).catch(() => {
      window.sessionStorage.removeItem("goalforge_session_initialized");
    });
  }, []);

  return null;
}
