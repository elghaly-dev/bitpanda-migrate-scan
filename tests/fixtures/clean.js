const BASE = "https://api.public.bitpanda.com/v1";
fetch(BASE + "/portfolio", {headers: {"x-api-key": process.env.BITPANDA_KEY}});
