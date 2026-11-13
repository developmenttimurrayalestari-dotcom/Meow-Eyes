'use strict';

// CRACO reads NODE_ENV before CRA's start script normalizes it. An inherited
// production environment would resolve the production React Refresh runtime
// while webpack still enables development refresh, crashing the browser.
process.env.NODE_ENV = 'development';
process.env.BABEL_ENV = 'development';

const entry = require.resolve('@craco/craco/dist/bin/craco.js');
process.argv = [process.execPath, entry, 'start'];
require(entry);
