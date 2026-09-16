export const downloadCSV = (data: any[], filename: string) => {
  if (!data || data.length === 0) {
    console.warn("No data to export");
    return;
  }

  // Extract headers
  const headers = Object.keys(data[0]);
  
  // Convert array of objects to CSV string
  const csvRows = [];
  
  // Add header row
  csvRows.push(headers.map(header => `"${header}"`).join(','));
  
  // Add data rows
  for (const row of data) {
    const values = headers.map(header => {
      const val = row[header];
      // Escape quotes and wrap in quotes
      const escaped = ('' + (val ?? '')).replace(/"/g, '""');
      return `"${escaped}"`;
    });
    csvRows.push(values.join(','));
  }
  
  const csvString = csvRows.join('\n');
  
  // Create blob and download link
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
