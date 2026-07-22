const pad = (value: number) => String(value).padStart(2, '0');

export const toRoutineTime = (value: string) => value.slice(11, 16);

export const toTodayDateTime = (time: string) => {
	const today = new Date();
	const date = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
	return `${date}T${time}`;
};

export const toMinutes = (time: string) => {
	const [hour, minute] = time.split(':').map(Number);
	return hour * 60 + minute;
};
