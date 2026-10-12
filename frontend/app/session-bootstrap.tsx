"use client";

import { useEffect } from "react";

import { API_URL } from "../lib/api/config";

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
