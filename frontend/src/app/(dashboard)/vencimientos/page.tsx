"use client";

import { useEffect, useState } from "react";

interface VencimientoItem {
  radicado: string | null;
  fecha_recibido: string | null;
  remitente: string | null;
  asunto: string | null;
  tipo_documental: string | null;
  plazo_dias_habiles: number;
  dias_habiles_restantes: number;
  es_urgente: boolean;
  entidad_detectada: string | null;
  palabra_clave_tutela: boolean;
  dependencia: string | null;
  estado: string | null;
  urgencia: "critica" | "alta" | "urgente" | "normal";
}

interface VencimientosResponse {
  items: VencimientoItem[];
  total: number;
  error?: string;
}

export default function VencimientosPage() {
  const [items, setItems] = useState<VencimientoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVencimientos();
  }, []);

  const fetchVencimientos = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/vencimientos/");
      const data: VencimientosResponse = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setItems(data.items);
      }
    } catch (e) {
      setError("Error al cargar vencimientos");
      console.error("Error fetching vencimientos:", e);
    } finally {
      setLoading(false);
    }
  };

  const urgenciaColors = {
    critica: "bg-red-100 text-red-800 border-red-200",
    alta: "bg-orange-100 text-orange-800 border-orange-200",
    urgente: "bg-purple-100 text-purple-800 border-purple-200",
    normal: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const urgenciaLabels = {
    critica: "🔴 Crítica",
    alta: "🟠 Alta",
    urgente: "🟣 Urgente",
    normal: "⚪ Normal",
  };

  const formatFecha = (fecha: string | null) => {
    if (!fecha) return "-";
    try {
      return new Date(fecha).toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch {
      return fecha;
    }
  };

  const getDiasClass = (dias: number) => {
    if (dias < 0) return "text-red-600 font-bold";
    if (dias <= 3) return "text-red-600 font-semibold";
    if (dias <= 7) return "text-orange-600 font-medium";
    return "text-green-600";
  };

  const getDiasLabel = (dias: number) => {
    if (dias < 0) return `${Math.abs(dias)} días vencido`;
    if (dias === 0) return "Vence hoy";
    return `${dias} días hábiles`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h2 className="text-red-800 font-semibold mb-2">Error</h2>
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Vencimientos - Peticiones</h1>
        <div className="flex gap-2 text-sm">
          <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Crítica (≤3 días)</span>
          <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded">Alta (≤7 días)</span>
          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">Urgente</span>
          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">Normal</span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="bg-white rounded-xl border p-12 text-center">
          <p className="text-gray-500 text-lg">No hay peticiones en el libro de radicación</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Radicado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Recibido</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Remitente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asunto</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plazo (días háb.)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Días Restantes</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Urgencia</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entidad / Tutela</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dependencia</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((item) => (
                <tr key={item.radicado || item.asunto} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">{item.radicado || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{formatFecha(item.fecha_recibido)}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">{item.remitente || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-md truncate" title={item.asunto || ""}>{item.asunto || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 text-center">{item.plazo_dias_habiles}</td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span className={getDiasClass(item.dias_habiles_restantes)}>
                      {getDiasLabel(item.dias_habiles_restantes)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${urgenciaColors[item.urgencia]}`}>
                      {urgenciaLabels[item.urgencia]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {item.palabra_clave_tutela && <span className="inline-flex items-center gap-1 text-red-600 font-medium">⚖️ Tutela</span>}
                    {item.entidad_detectada && !item.palabra_clave_tutela && (
                      <span className="inline-flex items-center gap-1 text-purple-600 font-medium">
                        {item.entidad_detectada.charAt(0).toUpperCase() + item.entidad_detectada.slice(1)}
                      </span>
                    )}
                    {!item.palabra_clave_tutela && !item.entidad_detectada && <span className="text-gray-400">-</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.dependencia || "-"}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.estado || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm">
        <p className="font-medium text-blue-800 mb-1">Para Claudia:</p>
        <p className="text-blue-700">
          Esta vista muestra todas las peticiones de derecho ordenadas por urgencia.
          Las filas en <span className="font-semibold text-red-600">rojo (Crítica)</span> requieren acción inmediata (≤3 días hábiles).
          Las peticiones con <span className="font-semibold text-purple-600">Tutela</span> o entidades de control
          (<span className="font-semibold">Contraloría, Procuraduría, Personería, Juzgado</span>)
          se marcan como <span className="font-semibold text-purple-600">Urgente</span> por ley.
        </p>
      </div>
    </div>
  );
}