<!-- Source: https://www.dicebear.com/guides/use-the-library-with-react/ -->
<!-- Documentation for DiceBear 10.5.0. The complete docs as one file: https://www.dicebear.com/llms-full.txt -->

# React avatar library: using DiceBear with React

DiceBear works in React via the JS library or the HTTP API. Use `useMemo` to
generate deterministic SVG profile pictures from a seed, or use the HTTP API as
a plain `<img src>` with no additional dependencies.

You can use DiceBear with React either via the
[JS-Library](https://www.dicebear.com/how-to-use/js-library/) or the [HTTP-API](https://www.dicebear.com/how-to-use/http-api/).

## With the JS library

```jsx
import { useMemo } from 'react';
import { Style, Avatar } from '@dicebear/core';
import lorelei from '@dicebear/styles/lorelei.json' with { type: 'json' };

const style = new Style(lorelei);

export default function UserAvatar({ seed = 'Alice' }) {
  const avatar = useMemo(() => {
    return new Avatar(style, {
      seed,
      size: 128,
      // ... other options
    }).toDataUri();
  }, [seed]);

  return <img src={avatar} alt="Avatar" />;
}
```

## With the HTTP API

```jsx
import { useMemo } from 'react';

export default function Avatar({ seed = 'Alice' }) {
  const avatar = useMemo(() => {
    const url = new URL('https://api.dicebear.com/10.x/lorelei/svg');
    url.searchParams.set('seed', seed);
    url.searchParams.set('size', '128');
    // ... other options
    return url.href;
  }, [seed]);

  return <img src={avatar} alt="Avatar" />;
}
```
