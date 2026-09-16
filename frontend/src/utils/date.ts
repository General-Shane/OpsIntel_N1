export const formatDateLocal = (dateString: string): string => {
  if (!dateString) return "N/A";
  
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;

  const options: Intl.DateTimeFormatOptions = { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric', 
    hour: 'numeric', 
    minute: '2-digit', 
    hour12: true 
  };
  
  return date.toLocaleString('en-US', options);
};
