"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState("");
  const router = useRouter();
  useEffect(() => {
    const u = localStorage.getItem("user");
    if (!u) router.push("/login");
    else setUser(u);
  }, []);
  return (
    <div>
      <header className="border-b bg-white p-4 flex justify-between">
        <span className="font-bold">RADIA - {user}</span>
        <button onClick={()=>{localStorage.clear(); router.push("/login")}} className="text-sm">Salir</button>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}
