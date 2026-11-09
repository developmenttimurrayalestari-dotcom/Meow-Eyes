import { TextDecoder, TextEncoder } from "util";
import { randomFillSync, randomUUID } from "crypto";

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;
global.IS_REACT_ACT_ENVIRONMENT = true;
Object.defineProperty(global, "crypto", {
  configurable: true,
  value: { getRandomValues: randomFillSync, randomUUID },
});
