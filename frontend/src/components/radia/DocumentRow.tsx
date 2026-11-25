export function DocumentRow({ doc }: any) {
  return <div className="border-b p-2 flex justify-between"><span>{doc?.asunto}</span><span className="text-xs bg-yellow-100 px-2 py-1 rounded">Revision</span></div>;
}
