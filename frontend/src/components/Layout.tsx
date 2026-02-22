import { NavLink, Outlet } from "react-router";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/", label: "Open Positions" },
  { to: "/history", label: "History" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const { signOut } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r bg-muted/40 p-4">
        <h2 className="mb-6 px-2 text-lg font-semibold">Wheelhouse</h2>
        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <Button
          variant="ghost"
          size="sm"
          className="mt-auto w-full justify-start text-muted-foreground"
          onClick={() => signOut()}
        >
          Sign Out
        </Button>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
