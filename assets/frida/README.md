# Frida Java bridge

`java-bridge.js` is the bundled Java bridge used by `ultra0.run_trial` with
Frida 17 and later. Frida 16 continues to use its built-in bridge. End users
only need Python dependencies; Node.js is needed only to rebuild this asset.

Upstream: https://github.com/frida/frida-java-bridge

Bundled versions:

- frida-java-bridge 7.1.0 (LGPL-2.0 WITH WxWindows-exception-3.1)
- buffer 6.0.3 (MIT)
- base64-js 1.5.1 (MIT)
- ieee754 1.2.1 (BSD-3-Clause)

The upstream sources are available from the corresponding versioned npm
archives, e.g. https://registry.npmjs.org/frida-java-bridge/-/frida-java-bridge-7.1.0.tgz.
The readable bundle retains upstream code without behavioral modifications.
License notices are in `THIRD_PARTY_LICENSES.md`.

To rebuild, use an empty temporary directory:

```sh
npm install --save-exact frida-java-bridge@7.1.0 buffer@6.0.3 base64-js@1.5.1 ieee754@1.2.1 esbuild@0.28.2
```

Create `bridge-entry.js` containing:

```js
import Java from 'frida-java-bridge';
globalThis.Java = Java;
```

Then run:

```sh
npx esbuild bridge-entry.js --bundle --format=iife --platform=neutral --target=es2020 --outfile=java-bridge.js
```

Copy the output to `assets/frida/java-bridge.js`. Do not minify it: readable
upstream source and the ability to rebuild/replace the bridge are intentional.
