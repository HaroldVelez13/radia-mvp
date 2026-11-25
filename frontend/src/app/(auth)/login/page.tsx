"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const router = useRouter();

  const handleLogin = () => {
    if ((user === "martha" || user === "claudia") && pass === "TAC2026") {
      localStorage.setItem("user", user);
      router.push("/");
    } else {
      alert("Credenciales invalidas - usa martha/TAC2026");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-96">
        <h1 className="text-2xl font-bold mb-2">RADIA</h1>
        <p className="text-sm text-zinc-500 mb-6">Radicacion Asistida - TAC</p>
        <input className="w-full border p-2 rounded mb-3" placeholder="Usuario" value={user} onChange={e=>setUser(e.target.value)} />
        <input className="w-full border p-2 rounded mb-4" type="password" placeholder="Contraseña" value={pass} onChange={e=>setPass(e.target.value)} />
        <button onClick={handleLogin} className="w-full bg-black text-white p-2 rounded-lg">Entrar</button>
        <p className="text-xs mt-4 text-zinc-400">Martha: martha / TAC2026<br/>Claudia: claudia / TAC2026</p>
      </div>
    </div>
  );
}
