export type NavigationItem = {
  href: string;
  label: string;
};

export type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Analyze",
    items: [
      { href: "/", label: "Overview" },
      { href: "/analyze", label: "Analyze" },
      { href: "/history", label: "History" },
      { href: "/review", label: "Review" },
    ],
  },
  {
    label: "Models",
    items: [
      { href: "/models", label: "Models" },
      { href: "/experiments", label: "Experiments" },
      { href: "/evaluation", label: "Evaluation" },
      { href: "/performance", label: "Performance" },
      { href: "/monitoring", label: "Monitoring" },
    ],
  },
  {
    label: "Data",
    items: [
      { href: "/data", label: "Data" },
      { href: "/about", label: "About" },
    ],
  },
];

export const navigationItems = navigationGroups.flatMap((group) => group.items);

export function isActiveNavigationPath(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}
