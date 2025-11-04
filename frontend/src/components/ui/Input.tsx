type Props = React.InputHTMLAttributes<HTMLInputElement>
export default function Input(props: Props) {
  return <input className="w-full rounded-md border px-3 py-2 focus:outline-none focus:ring" {...props} />
}