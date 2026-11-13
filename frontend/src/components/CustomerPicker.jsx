function CustomerPicker({ customers, value, onChange }) {
  return (
    <label className="customer-picker">
      <span>Demo customer</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {customers.map((customer) => (
          <option value={customer.id} key={customer.id}>
            {customer.name}
          </option>
        ))}
      </select>
    </label>
  );
}
export default CustomerPicker;
