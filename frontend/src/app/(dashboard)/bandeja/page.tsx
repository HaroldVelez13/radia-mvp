"use client";

import { useEffect, useState } from "react";

interface BandejaItem {
  archivo: string;
  fecha: string | null;
  remitente: string | null;
  asunto: string | null;
  tipo_documental: string | null;
  no_documento: string | null;
  nit: string | null;
  semaforo: "rojo" | "amarillo" | "verde" | "gris";
  motivo: string;
  observaciones: string[];
}

interface AnalisisResponse {
  items: BandejaItem[];
  total: number;
}

interface PendienteItem {
  consecutivo: string;
  fecha: string | null;
  remitente: string | null;
  nit_documento: string | null;
  tipo_documental: string | null;
  asunto: string | null;
  no_documento: string | null;
  valor_total: number | null;
  dependencia: string | null;
  fecha_vencimiento: string | null;
  estado: string;
  observaciones: string | null;
}

interface PendientesResponse {
  items: PendienteItem[];
  total: number;
}

type Tab = "analisis" | "pendientes";

export default function BandejaPage() {
  const [activeTab, setActiveTab] = useState<Tab>("analisis");
  const [items, setItems] = useState<BandejaItem[]>([]);
  const [pendientes, setPendientes] = useState<PendienteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<BandejaItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalisis();
    fetchPendientes();
  }, []);

  const fetchAnalisis = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/bandeja/analisis");
      const data: AnalisisResponse = await res.json();
      setItems(data.items);
    } catch (e) {
      console.error("Error fetching bandeja:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPendientes = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/bandeja/pendientes");
      const data: PendientesResponse = await res.json();
      setPendientes(data.items);
    } catch (e) {
      console.error("Error fetching pendientes:", e);
    }
  };

  const handleRowClick = (item: BandejaItem) => {
    setSelectedItem(item);
    setModalOpen(true);
  };

  const handleAprobar = async (consecutivo: string) => {
    setActionLoading(consecutivo);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/bandeja/revisar/${consecutivo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: "aprobar" }),
      });
      if (!res.ok) throw new Error("Error al aprobar");
      fetchPendientes();
    } catch (e) {
      console.error("Error aprobando:", e);
      alert("Error al aprobar");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRechazar = async (consecutivo: string) => {
    setActionLoading(consecutivo);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/bandeja/revisar/${consecutivo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: "rechazar" }),
      });
      if (!res.ok) throw new Error("Error al rechazar");
      fetchPendientes();
    } catch (e) {
      console.error("Error rechazando:", e);
      alert("Error al rechazar");
    } finally {
      setActionLoading(null);
    }
  };

  const semaforoColors = {
    rojo: "bg-red-100 text-red-800 border-red-200",
    amarillo: "bg-yellow-100 text-yellow-800 border-yellow-200",
    verde: "bg-green-100 text-green-800 border-green-200",
    gris: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const semaforoLabels = {
    rojo: "🔴 Riesgo Alto",
    amarillo: "🟡 Revisar",
    verde: "🟢 OK",
    gris: "⚪ Error",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Bandeja de Entrada</h1>
        <div className="flex gap-2 text-sm">
          <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Rojo: Riesgo</span>
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Amarillo: Revisar</span>
          <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Verde: OK</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab("analisis")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "analisis"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Análisis ({items.length})
        </button>
        <button
          onClick={() => setActiveTab("pendientes")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "pendientes"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Pendientes ({pendientes.length})
        </button>
      </div>

      {/* Análisis Tab */}
      {activeTab === "analisis" && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Archivo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Remitente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asunto</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NIT / Doc</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Semáforo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((item) => (
                <tr
                  key={item.archivo}
                  onClick={() => handleRowClick(item)}
                  className="cursor-pointer hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">{item.archivo}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.fecha ? item.fecha.split("T")[0] : "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">{item.remitente || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-md truncate" title={item.asunto || ""}>{item.asunto || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.tipo_documental || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.nit || item.no_documento || "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${semaforoColors[item.semaforo]}`}>
                      {semaforoLabels[item.semaforo]}
                    </span>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">No hay correos en la bandeja</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pendientes Tab */}
      {activeTab === "pendientes" && (
        <div className="bg-white rounded-xl border overflow-hidden">
          {pendientes.length === 0 ? (
            <div className="px-4 py-12 text-center text-gray-500">
              No hay radicados pendientes de revisión
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Consecutivo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Remitente</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asunto</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NIT / Doc</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motivo revisión</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pendientes.map((item) => (
                  <tr key={item.consecutivo} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">{item.consecutivo}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.fecha ? item.fecha.split("T")[0] : "-"}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">{item.remitente || "-"}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-md truncate" title={item.asunto || ""}>{item.asunto || "-"}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.tipo_documental || "-"}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.nit_documento || item.no_documento || "-"}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate" title={item.observaciones || ""}>
                      {item.observaciones || "-"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAprobar(item.consecutivo)}
                          disabled={actionLoading === item.consecutivo}
                          className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                          {actionLoading === item.consecutivo ? "⏳" : "✓ Aprobar"}
                        </button>
                        <button
                          onClick={() => handleRechazar(item.consecutivo)}
                          disabled={actionLoading === item.consecutivo}
                          className="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
                        >
                          {actionLoading === item.consecutivo ? "⏳" : "✗ Rechazar"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Modal Por Qué */}
      {modalOpen && selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setModalOpen(false)}>
          <div className="fixed inset-0 bg-black/50" />
          <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-xl font-semibold">Por qué: {semaforoLabels[selectedItem.semaforo]}</h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Archivo:</span> <span className="font-mono ml-2">{selectedItem.archivo}</span></div>
                <div><span className="text-gray-500">Fecha:</span> <span className="ml-2">{selectedItem.fecha ? selectedItem.fecha.split("T")[0] : "-"}</span></div>
                <div><span className="text-gray-500">Remitente:</span> <span className="ml-2">{selectedItem.remitente || "-"}</span></div>
                <div><span className="text-gray-500">Tipo:</span> <span className="ml-2">{selectedItem.tipo_documental || "-"}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Asunto:</span> <p className="mt-1">{selectedItem.asunto || "-"}</p></div>
                <div><span className="text-gray-500">NIT / Doc:</span> <span className="ml-2">{selectedItem.nit || selectedItem.no_documento || "-"}</span></div>
              </div>

              <div className="border-t pt-4">
                <h3 className="font-medium mb-2">Motivo del semáforo:</h3>
                <p className="bg-gray-50 p-3 rounded-lg text-sm">{selectedItem.motivo}</p>
              </div>

              {selectedItem.observaciones.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Observaciones detalladas:</h3>
                  <ul className="space-y-1 text-sm">
                    {selectedItem.observaciones.map((obs, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700">
                        <span className="text-blue-500 mt-0.5">•</span>
                        <span>{obs}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="p-6 border-t flex justify-end">
              <button
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}