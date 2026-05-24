

export type Tenant = {
  id: string;
  name: string;
};

type Props = {
  tenants: Tenant[];
  selected?: string;
  onSelect?: (id: string) => void;
};

export default function OrgSwitcher({ tenants, selected, onSelect }: Props) {
  return (
    <div className="org-switcher">
      <label className="label">Workspace</label>
      <select
        value={selected}
        onChange={(e) => onSelect?.(e.target.value)}
        className="select"
      >
        {tenants.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
    </div>
  );
}
