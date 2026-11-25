export default function Dashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Bandeja de Radicacion</h1>
      <p className="text-zinc-500 mt-2">Aqui Martha vera los 16 correos con semaforo de confianza y boton Aprobar.</p>
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl shadow">Total: 16 docs</div>
        <div className="bg-white p-4 rounded-xl shadow">Por revisar: 3</div>
        <div className="bg-white p-4 rounded-xl shadow">Vence esta semana: 5</div>
      </div>
    </div>
  );
}
