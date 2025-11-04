type Props = { children: React.ReactNode } & React.ButtonHTMLAttributes<HTMLButtonElement>
export default function Button({ children, className = '', ...rest }: Props) {
  return (
    <button className={`px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 ${className}`} {...rest}>
      {children}
    </button>
  )
}