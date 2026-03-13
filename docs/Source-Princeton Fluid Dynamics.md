# 8.1 HYDROSTATICS: FLUIDS AT REST

In this section and the next, we'll discuss some of the fundamental concepts dealing with substances that can flow, which are known as **fluids**. *Both liquids and gases are fluids*, but there are distinctions between them. At the molecular level, a substance in the liquid phase is similar to one in the solid phase in that the molecules are close to, and interact with, one another. The molecules in a liquid are able to move around a little more freely than those in a solid, in which the molecules typically only vibrate around relatively fixed positions. By contrast, the molecules of a gas are not constrained and fly around in a chaotic swarm, with hardly any interaction. On a macroscopic level, there is another distinction between liquids and gases. If you pour a certain volume of a liquid into a container of a greater volume, the liquid will occupy its original volume, whatever the shape and size of the container. However, if you introduce a sample of gas into a container, the molecules will fly around and fill the *entire* container.

## Density and Specific Gravity

The **density** of a substance is the amount of mass contained in a unit of volume. In SI units, density is usually expressed in kg/m<sup>3</sup> or g/cm<sup>3</sup>.

> $$ \text{density} = \frac{\text{mass}}{\text{volume}} $$
> $$ \rho = \frac{m}{V} $$

There is one substance whose density you should memorize: The density of liquid water is taken to be 1000 kg/m<sup>3</sup> or 1 g/cm<sup>3</sup>. (Another useful version of the same value: 1 kg/L, where L stands for a liter; a liter is 1000 cm<sup>3</sup>.)

Sometimes the MCAT mentions **specific gravity**. This (poorly named) unitless number tells us how dense something is compared to water:

> $$ \text{specific gravity} = \frac{\text{density of substance}}{\text{density of water}} $$
> $$ \text{sp. gr} = \frac{\rho}{\rho_{\text{H}_2\text{O}}} $$

---

For solids, density doesn’t change much with surrounding pressure or temperature. For example, the density of marble is pretty close to 2700 kg/m<sup>3</sup> under most conditions. Liquids behave the same way: the density of water is pretty close to 1000 kg/m<sup>3</sup> under all conditions at which it’s a liquid. However, the density of a gas changes markedly with pressure and temperature. (The ideal gas law tells us that $PV = nRT$, so the density of a sample of an ideal gas is given by the equation $\rho_{\text{gas}} = m/V = mp / nRT$, which depends on $P$ and $T$.)

**Example 8-1:** Turpentine has a specific gravity of 0.9. What is the density of this liquid?

**Solution:** By definition, we have

$$\rho_{\text{turpentine}} = (\text{sp. gr.}_{\text{turpentine}})(\rho_{\text{H}_2\text{O}}) = (0.9)(1000 \frac{\text{kg}}{\text{m}^3}) = 900 \frac{\text{kg}}{\text{m}^3}$$

**Example 8-2:** A 2 cm<sup>3</sup> sample of osmium, one of the densest substances on Earth, has a mass of 45 g. What’s the specific gravity of this metal?

**Solution:** The density of osmium is

$$\rho = \frac{m}{V} = \frac{45 \text{ g}}{2 \text{ cm}^3} = 22.5 \frac{\text{g}}{\text{cm}^3}$$

Since this is 22.5 times the density of water (which is 1 g/cm<sup>3</sup>), the specific gravity of osmium is 22.5.

**Example 8-3:** A cork has volume of 4 cm<sup>3</sup> and weighs 0.01 N. What is its density? What is its specific gravity?

**Solution:** Because the cork weighs 10<sup>-2</sup> N, its mass is

$$m = \frac{w}{g} = \frac{10^{-2} \text{ N}}{10 \frac{\text{N}}{\text{kg}}} = 10^{-3} \text{ kg}$$

Therefore, its density is

$$\rho_{\text{cork}} = \frac{m}{V} = \frac{10^{-3} \text{ kg}}{4 \text{ cm}^3} \times \left( \frac{10^2 \text{ cm}}{1 \text{ m}} \right)^3 = \frac{1}{4} \times 10^3 \frac{\text{kg}}{\text{m}^3} = 2.5 \times 10^2 \frac{\text{kg}}{\text{m}^3}$$

---

and its specific gravity is

$$ \text{sp. gr.}_{\text{cork}} = \frac{\rho_{\text{cork}}}{\rho_{\text{H}_2\text{O}}} = \frac{\frac{1}{4} \times 10^3 \frac{\text{kg}}{\text{m}^3}}{10^3 \frac{\text{kg}}{\text{m}^3}} = \frac{1}{4} = 0.25 $$

## Force of Gravity for Fluids
When solving questions involving fluids, it is often handy to know how to find the force of gravity acting on the fluid itself or objects that are immersed in the fluid. In previous chapters, we have used $F_{\text{grav}} = mg$ without too much difficulty. However, with fluids, it is more difficult to remove a portion of fluid from a tank, place it on a scale, and find its mass. Using the relationship between mass, volume, and density, we can redefine the magnitude of $F_{\text{grav}}$ for fluids questions:

$$ \rho = \frac{m}{V} \rightarrow m = \rho V \rightarrow \therefore F_{\text{grav}} = mg = \rho Vg $$

With this new formula $F_{\text{grav}} = \rho Vg$, it is important to make sure that the density ($\rho$) and the volume ($V$) describe the properties of the correct object or fluid.

## Pressure
If we place an object in a fluid, the fluid exerts a contact force on the object. If we look at how that force is *distributed* over any small area of the object's surface, we have the concept of **pressure**:

> ### Pressure
> $$ P = \frac{\text{force}_{\perp}}{\text{area}} = \frac{F_{\perp}}{A} $$

The subscript $\perp$ (which means "perpendicular") indicates that pressure is defined as the magnitude of the force acting *perpendicular* to the surface, divided by the area. We don't need to worry very much about this, because (for MCAT purposes) at any given point in a fluid the pressure is the same in all directions, which means that the force does not depend on the orientation of the force.

---

Although the formula for pressure involves "force," pressure is actually a *scalar quantity*, because the perpendicular force is the same for all orientations of surface. The unit of pressure is the N/m<sup>2</sup>, which is called a **pascal** (abbreviated **Pa**). Because 1 N is a pretty small force and 1 m<sup>2</sup> is a pretty big area, 1 Pa is very small. Often, you'll see pressure expressed in kPa (or even in MPa). For example, at sea level, normal atmospheric pressure is about 100 kPa.

Let's imagine we have a tank of water with a lid on top. Suspended from the lid is a string attached to a thin metal sheet. The figures on the following page show you two views of this.

![Front view of a tank of water with a lid, a string, and a metal sheet.](image)
![Side corner view of a tank of water with a lid, a string, and a metal sheet.](image)

front view side corner view

The weight of the water above the metal sheet produces a force that pushes down on the sheet. If we divide this force by the area of the sheet, $w/A$, we get the pressure, due to the water, on the sheet. The formula for calculating this pressure depends on the density of the fluid in the tank ($\rho_{\text{fluid}}$), the depth of the sheet ($D$), and the acceleration due to gravity ($g$).

$$P = \frac{w_{\text{fluid}}}{A} = \frac{m_{\text{fluid}}g}{A} = \frac{\rho_{\text{fluid}}V_{\text{fluid}}g}{A} = \frac{\rho_{\text{fluid}}ADg}{A} = \rho_{\text{fluid}}Dg$$

<mark>**Hydrostatic Gauge Pressure**
$$P_{\text{gauge}} = \rho_{\text{fluid}}gD$$</mark>

---

This formula gives the pressure due only to the fluid (in this case, the water) in the tank. This is called **hydrostatic gauge pressure**. It's called hydrostatic, because the fluid is at rest, and *gauge* pressure means that we don't take the pressure due to the atmosphere into account. If there were no lid on the water tank, then the water would be exposed to the atmosphere, and the *total* pressure at any point in the water would be equal to the atmospheric pressure pushing down on the surface *plus* the pressure due to the water (that is, the gauge pressure). So, below the surface, we'd have

$$P_{\text{total}} = P_{\text{atm}} + P_{\text{gauge}}$$

If the tank were closed to the atmosphere, but there were a layer of gas above the surface of the water, then the total pressure at a point below the surface would be the pressure of the gas pushing down at the surface plus the gauge pressure: $P_{\text{total}} = P_{\text{gas}} + P_{\text{gauge}}$. In general, we'll have

$$P_{\text{total}} = P_{\text{at surface}} + P_{\text{gauge}}$$

![Two diagrams of tanks filled with water. The left tank is open to the atmosphere, showing $P_{\text{atm}}$ pushing down on the surface and $P_{\text{gauge}}$ acting within the fluid, with the equation $P_{\text{total}} = P_{\text{atm}} + P_{\text{gauge}}$ below it. The right tank is closed with a layer of gas above the water, showing $P_{\text{gas}}$ pushing down on the surface and $P_{\text{gauge}}$ acting within the fluid, with the equation $P_{\text{total}} = P_{\text{gas}} + P_{\text{gauge}}$ below it.](image)

in either case:

$$P_{\text{total}} = P_{\text{at surface}} + P_{\text{gauge}}$$

Notice that hydrostatic gauge pressure, $P_{\text{gauge}} = \rho_{\text{fluid}}gD$, is proportional to both the depth and the density of the fluid. *Total* pressure, however, is *not* proportional to either of these quantities if $P_{\text{on surface}}$ isn't zero.

---

![Two graphs comparing gauge pressure and total pressure versus depth. The first graph shows a line starting at the origin labeled P_gauge, with a note: "This is the graph of a proportion." The second graph shows a line starting above the origin at P_at surface, labeled P_total, with a note: "This is not the graph of a proportion (because the line doesn't go through the origin)."](image)

The lines in these graphs will be straight as long as the density of the liquid remains constant as the depth increases. Actually, $\rho$ increases as the depth increases, but the effect is small enough that we generally consider liquids to be **incompressible**; that is, that the density of a liquid remains constant (so, in particular, the density doesn't increase with depth).

**Example 8-4:** The density of seawater is $1025\text{ kg/m}^3$. Consider a point X that's $10\text{ m}$ below the surface of the ocean.

a) What's the gauge pressure at X?
b) If the atmospheric pressure is $1.015 \times 10^5\text{ Pa}$, what is the total pressure at X?
c) Consider a point Y that's $50\text{ m}$ below the surface. How does the gauge pressure at Y compare to the gauge pressure at X? How does the total pressure at Y compare to the total pressure at X?

**Solution:**

a) The gauge pressure at X is
$$P_{\text{gauge}} = \rho_{\text{fluid}}gD = (1025\frac{\text{kg}}{\text{m}^3})(10\frac{\text{N}}{\text{kg}})(10\text{ m}) = 1.025 \times 10^5\text{ pa}$$

b) The total pressure at X is the atmospheric pressure plus the gauge pressure:
c) Since $P_{\text{gauge}}$ is proportional to $D$, an increase in $D$ by a factor of 5 will mean the gauge pressure will also increase by a factor of 5. Therefore, the gauge pressure at Y will be $5(P_{\text{gauge at X}}) = 5.125 \times 10^5$. The total pressure at Y is equal to the atmospheric pressure plus the gauge pressure at Y, so
$$P_{\text{total at Y}} = P_{\text{atm}} + P_{\text{gauge}} = (1.015 \times 10^5\text{ pa}) + (1.025 \times 10^5\text{ pa})$$

---



Notice that P<sub>total</sub> at y is not 5 times P<sub>total</sub> at X. **Total pressure is not proportional to depth.**

## Example 8-5

A large storage tank fitted with a tight lid holds a liquid. The space between the surface of the liquid and the lid of the tank is filled with molecules of the stored liquid in the gaseous phase. At a depth of 40 m, the total pressure is 520 kPa, while at a depth of 50 m, the total pressure is 600 kPa. What's the pressure of the gas above the surface of the liquid?

**Solution:** Let P<sub>gas</sub> be the pressure that the gas exerts on the surface of the liquid. Then we have

$$P_{\text{total at } D_1 = 40 \text{ m}} = P_{\text{gas}} + \rho_{\text{fluid}}gD_1 = P_{\text{gas}} + \rho_{\text{fluid}}g(40 \text{ m}) = 520 \text{ kPa}$$

$$P_{\text{total at } D_i = 50 \text{ m}} = P_{\text{gas}} + \rho_{\text{fluid}}gD_2 = P_{\text{gas}} + \rho_{\text{fluid}}g(50 \text{ m}) = 600 \text{ kPa}$$

We have two equations and two unknowns (P<sub>gas</sub> and ρ<sub>fluid</sub>). If we subtract the first equation from the second, we get ρ<sub>fluid</sub>g(10 m) = 80 kPa, which tells us that ρ<sub>fluid</sub>g = 8 kP/m. Plugging this back into either one of the equations will give us P<sub>gas</sub>. Choosing, say, the first one, we find that

$$P_{\text{gas}} + \left(8 \frac{\text{kPa}}{\text{m}}\right)(40 \text{ m}) = 520 \text{ kPa} \rightarrow P_{\text{gas}} = 200 \text{ kPa}$$

## Example 8-6

The containers shown below are all filled with the same liquid. At which point (A, B, C, D, E, or F) is the gauge pressure the lowest?

<table>
<tr>
<td colspan="3" style="text-align: center; padding: 20px;">
[Container 1: Wide rectangular tank with dashed vertical line labeled "D" showing depth, points A and B marked at liquid surface level on left and right sides]
</td>
<td colspan="3" style="text-align: center; padding: 20px;">
[Container 2: Tall narrow cylindrical container with point C marked at liquid surface level]
</td>
<td colspan="3" style="text-align: center; padding: 20px;">
[Container 3: Container with step/varying depth, points D, E, F marked at liquid surface level across left, middle, and right]
</td>
</tr>
<tr>
<td style="text-align: center;">A</td>
<td style="text-align: center;">B</td>
<td style="text-align: center;">C</td>
<td style="text-align: center;">D</td>
<td style="text-align: center;">E</td>
<td style="text-align: center;">F</td>
</tr>
</table>



---

**Solution:** It’s important to remember that the formula $$P_{\text{gauge}} = \rho_{\text{fluid}}gD$$ applies regardless of the shape of the container in which the fluid is held. If all the containers are filled with the same fluid, then the pressure is the *same* everywhere along the horizontal dashed line. This is because every point on this line (and within one of the containers) is at the same depth, $D$, below the surface of the fluid. The fact that the first container is wide, the second container is narrow, and the third container is wide at the base but has a narrow neck makes no difference. Even the fact that Points D and F (in the third container) aren’t *directly* underneath a column of fluid of height $D$ makes no difference either.

Pressure is the magnitude of the force per area, so pressure is a *scalar*. Pressure has no direction. The force *due to the pressure* is a vector, however, and the direction of this force on any small surface is always perpendicular to that surface. For example, in the figure below, the pressure at Point A is the same as the pressure at Point B, because they’re at the same depth. But, as you can see, the direction of the force due to the pressure varies depending on the orientation of the surface (and even which side of the surface) the force is pushing on.

![Diagram of a tank of water showing various points (A, B, D) and surfaces with arrows representing the direction of force due to pressure, which is always perpendicular to the surface regardless of orientation.](image)

# Buoyancy and Archimedes’ Principle

Let’s place a wooden block in our tank of water. Since the pressure on each side of the block depends on its average depth, we see that there’s more pressure on the bottom of the block than there is on the top of it. Therefore, there’s a greater force pushing up on the bottom of the block than there is pushing down on the top. The forces due to the pressure on the other four sides (left and right, front and back) cancel out, so the net fluid force on the block is upward. This net upward fluid force is called the **buoyant force** (or just **buoyancy** for short), which we’ll denote by $F_{\text{Buoy}}$ (or $F_{\text{B}}$).

---

We can calculate the magnitude of the buoyant force using Archimedes' principle:

> ### <span style="color: green">Archimedes' Principle</span>
> *The magnitude of the buoyant force is equal to the weight of the fluid displaced by the object.*

When an object is partially or completely submerged in a fluid, the volume of the object that's submerged, which we call $V_{\text{sub}}$, is the volume of the fluid displaced.

![A rectangular object floating in a tank of liquid. The portion of the object below the water line is shaded grey and labeled $V_{\text{sub}}$ with a bracket. The total height of the object is labeled $V$ with a bracket. The container is labeled "tank of liquid".](image)

By multiplying $V_{\text{sub}}$ by the density of the fluid, we get the *mass* of the fluid displaced; then, multiplying this mass by $g$ gives us the weight of the fluid displaced. So, here's Archimedes' principle as a mathematical equation:

> ### <span style="color: green">Archimedes' Principle</span>
> $$F_{\text{Buoy}} = \rho_{\text{fluid}} V_{\text{sub}} g$$

When an object floats, its submerged volume is just enough to make the buoyant force it feels balance its weight. That is, for a floating object, we always have $w_{\text{object}} = F_{\text{Buoy}}$. If an object's density is $\rho_{\text{object}}$ and its volume is $V$, its weight will be $\rho_{\text{object}} V_{\text{object}} g$. The buoyant force it feels is $\rho_{\text{fluid}} V_{\text{sub}} g$. Setting these equal to each other, we find that

---

<mark>**Floating Object in Equilibrium on Surface**</mark>
$$w_{\text{object}} = F_{\text{Buoy}}$$
$$\frac{V_{\text{sub}}}{V} = \frac{\rho_{\text{object}}}{\rho_{\text{fluid}}}$$

So, if $\rho_{\text{object}} < \rho_{\text{fluid}}$, then the object will float; and the fraction of its volume that's submerged is the same as the ratio of its density to the fluid's density. *This is a very helpful fact to know for the MCAT.* For example, if the object's density is 3/4 the density of the fluid, then 3/4 of the object will be submerged (and vice versa).

If an object is denser than the fluid, then the object will sink. In this case, even if the entire object is submerged (in an attempt to maximize the buoyant force), the object's weight is still greater than the buoyant force. This leaves a net force in the downwards direction, causing the object to sink by accelerating downwards. If an object just happens to have the same density as the fluid, it will be happy hovering (in static equilibrium) underneath the fluid.

For an object that is completely submerged in the surrounding fluid, the actual weight of the object ($w_{\text{object}}Vg$) remains unchanged. However, the object's "apparent" weight is less due to the buoyant force "buoying" the object upwards. This corresponds to the measurement of a scale placed at the bottom of a tank of liquid in order to measure the apparent weight of the submerged object, or the normal force acting on the object.

Since the volume of the object is equal to the submerged volume ($V = V_{\text{sub}}$), the buoyant force $F_{\text{Buoy}}$ on the object is equal to $\rho_{\text{fluid}}Vg$. Therefore,

$$\frac{w_{\text{object}}}{F_{\text{Buoy}}} = \frac{\rho_{\text{object}}Vg}{\rho_{\text{fluid}}Vg} = \frac{\rho_{\text{object}}}{\rho_{\text{fluid}}}$$

If the fluid in which the object is submerged is water, the ratio of the object weight to the buoyant force is equal to the specific gravity of the object.

**Example 8-7:** Ethyl alcohol has a specific gravity of 0.8. If a cork of specific gravity 0.25 floats in a beaker of ethyl alcohol, what fraction of the cork's volume is submerged?

A. 4/25

---

B. 1/5
C. 1/4
D. 5/16

**Solution:** Because the cork has a lower density than the ethyl alcohol, we know that the cork will float. Furthermore, the fraction of the cork's volume that will be submerged is

$$ \frac{V_{\text{sub}}}{V} = \frac{\rho_{\text{object}}}{\rho_{\text{fluid}}} = \frac{(0.25)\rho_{\text{H}_2\text{O}}}{(0.8)\rho_{\text{H}_2\text{O}}} = \frac{0.25}{0.8} = \frac{1/4}{4/5} = \frac{5}{16} $$

Therefore, the answer is D.

**Example 8-8:** The density of ice is $920 \text{ kg/m}^3$, and the density of seawater is $1025 \text{ kg/m}^3$. Approximately what percent of an iceberg floats above the surface of the ocean (in other words, how much is "the tip of the iceberg")?

A. 5%
B. 10%
C. 90%
D. 95%

**Solution:** Because the ice has a lower density than the seawater, we know that the iceberg will float. Furthermore, the fraction of the iceberg's volume that will be submerged is

$$ \frac{V_{\text{sub}}}{V} = \frac{\rho_{\text{object}}}{\rho_{\text{fluid}}} = \frac{920 \frac{\text{kg}}{\text{m}^3}}{1025 \frac{\text{kg}}{\text{m}^3}} \approx \frac{900}{1000} = 90\% $$

However, the answer is not C. The question asked what percent of the iceberg floats *above* the surface. So, if 90% is submerged, then 10% is above the surface, and the answer is B. Watch for this kind of tricky wording; it is a common MCAT tactic.

**Example 8-9:** A glass sphere of specific gravity 2.5 and volume $10^{-3} \text{ m}^3$ is completely submerged in a large container of water. What is the apparent weight of the sphere while immersed?

**Solution:** Because the buoyant force pushes up on the object, the object's *apparent weight*, $w_{\text{apparent}} = w - F_{\text{Buoy}}$, is less than its true weight, $w$. Because the sphere is completely submerged, we have $V_{\text{sub}} = V$, so the buoyant force on the sphere is

---

$$ F_{\text{Buoy}} = \rho_{\text{fluid}} V_{\text{sub}} g $$
$$ = \rho_{\text{H}_2\text{O}} V g $$
$$ = (1000 \frac{\text{kg}}{\text{m}^3})(10^{-3} \text{ m}^3)(10 \frac{\text{N}}{\text{kg}}) $$
$$ = 10 \text{ N} $$

The true weight of the glass sphere is

$$ w = \rho_{\text{glass}} V g $$
$$ = (\text{sp. gr.}_{\text{glass}} \times \rho_{\text{H}_2\text{O}}) V g $$
$$ = (2.5 \times 1000 \frac{\text{kg}}{\text{m}^3})(10^{-3} \text{ m}^3)(10 \frac{\text{N}}{\text{kg}}) $$
$$ = 25 \text{ N} $$

Therefore, the apparent weight of the sphere while immersed is

$$ w_{\text{apparent}} = w - F_{\text{Buoy}} = 25 \text{ N} - 10 \text{ N} = 15 \text{ N} $$

**Example 8-10:** An object weighs 50 N, but weighs only 30 N when it's completely immersed in a liquid of specific gravity 0.8. What's the specific gravity of this object?

**Solution:** The weight of the object is $w_{\text{object}} = \rho_{\text{object}} V g$, and the buoyant force it feels when completely immersed (that is, when $V_{\text{sub}} = V$) is $F_{\text{Buoy}} = \rho_{\text{fluid}} V g$. Therefore,

$$ \frac{w_{\text{object}}}{F_{\text{Buoy}}} = \frac{\rho_{\text{object}} V g}{\rho_{\text{fluid}} V g} = \frac{\rho_{\text{object}}}{\rho_{\text{fluid}}} $$

Now, since this 50 N object weighs only 30 N when immersed, the buoyant force must be 20 N. So, we can write

$$ \frac{w_{\text{object}}}{F_{\text{Buoy}}} = \frac{50 \text{ N}}{20 \text{ N}} = \frac{5}{2} $$

---

We now have two expressions for the ratio $w_{\text{object}} / F_{\text{Buoy}}$. Therefore,

$$\frac{\rho_{\text{object}}}{\rho_{\text{fluid}}} = \frac{5}{2}$$

If the object's density is 5/2 times the fluid's density, then the object's specific gravity is 5/2 times the fluid's specific gravity; that is,

$$\text{sp. gr.}_{\text{object}} = \frac{5}{2}(\text{sp.gr.}_{\text{fluid}}) = \frac{5}{2}(0.8) = 2$$

**Example 8-11:** A balloon that weighs 0.18 N is then filled with helium so that its volume becomes 0.03 m<sup>3</sup>. (Note: The density of helium is 0.2 kg/m<sup>3</sup>.)

a) What is the net force on the balloon if it's surrounded by air? (Note: The density of air is 1.2 kg/m<sup>3</sup>.)
b) What will be the initial upward acceleration of the balloon if it's released from rest?

**Solution:**

a) Remember that gases are fluids, so they also exert buoyant forces. If an object is immersed in a gas, the object experiences a buoyant force equal to the weight of the gas it displaces. In this case, the balloon is completely immersed in a "sea" of air (so $V_{\text{sub}} = V$), and Archimedes' principle tells us that the buoyant force on the balloon due to the surrounding air is

---

![Free body diagram of a balloon showing the upward buoyant force $F_{\text{Buoy}}$ and the downward gravitational force $F_{\text{grav}} = w$.](image)

$$ F_{\text{Buoy}} = \rho_{\text{fluid}} V_{\text{sub}} g $$
$$ = \rho_{\text{air}} V g $$
$$ = (1.2 \frac{\text{kg}}{\text{m}^3})(0.03 \text{ m}^3)(10 \frac{\text{N}}{\text{kg}}) $$
$$ = 0.36 \text{ N} $$

The weight of the inflated balloon is equal to the weight of the balloon material (0.18 N) plus the weight of the helium:

$$ w_{\text{total}} = w_{\text{material}} + w_{\text{helium}} $$
$$ = w_{\text{material}} + \rho_{\text{helium}} V g $$
$$ = 0.18 \text{ N} + (0.2 \frac{\text{kg}}{\text{m}^3})(0.03 \text{ m}^3)(10 \frac{\text{N}}{\text{kg}}) $$
$$ = 0.18 \text{ N} + 0.06 \text{ N} $$
$$ = 0.24 \text{ N} $$

Because $F_{\text{Buoy}} > w_{\text{total}}$, the net force on the balloon is upward and has magnitude

$$ F_{\text{net}} = F_{\text{Buoy}} - w_{\text{total}} = (0.36 \text{ N}) - (0.24 \text{ N}) = 0.12 \text{ N} $$

b) Using Newton's second law, $a = F_{\text{net}} / m$ we find that

---

$$ a = \frac{F_{\text{net}}}{m} = \frac{F_{\text{net}}}{\frac{w}{g}} = \frac{0.12 \text{ N}}{\left( \frac{0.24 \text{ N}}{10 \text{ m/s}^2} \right)} = \frac{(0.12 \text{ N}) \cdot (10 \text{ m/s}^2)}{0.24 \text{ N}} = \frac{10 \text{ m/s}^2}{2} = 5 \text{ m/s}^2 $$

# Pascal’s Law

Pascal’s law is a statement about fluid pressure. It says that a confined fluid will transmit an externally applied pressure change to all parts of the fluid and the walls of the container without loss of magnitude. In less formal language, if you squeeze a container of fluid, the fluid will transmit your squeeze perfectly throughout the container. The most important application of Pascal’s law is to hydraulics.

Consider a simple hydraulic jack consisting of two pistons resting above two cylindrical vessels of fluid that are connected by a pipe. If you push down on one piston, the other one will rise. Let’s make this more precise. Let $F_1$ be the magnitude of the force you exert down on one piston (whose cross-sectional area is $A_1$) and let $F_2$ be the magnitude of the force that the other piston (cross-sectional area $A_2$) exerts upward as a result.

![A diagram of a hydraulic system showing two connected cylinders of different widths filled with fluid. A downward force $F_1$ is applied to a piston of area $A_1$ on the left, and an upward force $F_2$ is exerted by a piston of area $A_2$ on the right.](image)

Pushing down on the left-hand piston with a force $F_1$ introduces a pressure increase of $F_1 / A_1$. Pascal’s law tells us that this pressure change is transmitted, without loss of magnitude, by the fluid to the other end. Since the pressure change at the other piston is $F_1 / A_1$, we have, by Pascal’s law,

$$ \frac{F_1}{A_1} = \frac{F_2}{A_2} $$

---

Solving this equation for $F_2$, we get

$$F_2 = \frac{A_2}{A_1} F_1$$

So, if $A_2$ is greater than $A_1$ (as it is in the figure), then the ratio of the areas, $A_2 / A_1$, will be greater than 1, so $F_2$ will be greater than $F_1$; that is, *the output force, $F_2$, is greater than your input force, $F_1$*. This is why hydraulic jacks are useful; we end up lifting something very heavy (a car, for example) by exerting a much smaller force (one that would be insufficient to lift the car if it were just applied directly to the car).

This seems too good to be true; doesn't this violate some conservation law? No, since there's no such thing as a "Conservation of Force" law. However, there is a price to be paid for the magnification of the force. Let's say you push the left-hand piston down by a distance $d_1$, and that the distance the right-hand piston moves upward is $d_2$. Assuming the fluid is incompressible, whatever fluid you push out of the left-hand cylinder must appear in the right-hand cylinder. Since volume is equal to cross-sectional area times distance, the volume of the fluid you push out of the left-hand cylinder is $A_1d_1$, and the extra volume of fluid that appears in the right-hand cylinder is $A_2d_2$.

![Diagram of a hydraulic system showing two connected cylinders of different cross-sectional areas $A_1$ and $A_2$ filled with fluid. A downward force $F_1$ is applied to the smaller piston, moving it down a distance $d_1$. This results in an upward force $F_2$ on the larger piston, moving it up a distance $d_2$.](image)

But these volumes have to be the same, so $A_1d_1 = A_2d_2$. Solving this equation for $d_2$, we get

$$d_2 = \frac{A_1}{A_2} d_1$$

---

If the area of the right-hand piston ($A_2$) is greater than the area of the left-hand piston ($A_1$), the ratio $A_1 / A_2$ will be *less* than 1, so $d_2$ will be less than $d_1$. In fact, the decrease in $d$ is the same as the increase in $F$. For example, if $A_2$ is five times larger than $A_1$, then $F_2$ will be five times greater than $F_1$, but $d_2$ will only be *one-fifth* of $d_1$. We can now see that the product of $F$ and $d$ will be the same for both pistons:

$$F_2 d_2 = \left( \frac{A_2}{A_1} F_1 \right) \cdot \left( \frac{A_1}{A_2} d_1 \right) = F_1 d_1$$

Recall that the product of $F$ and $d$ is the amount of work done. What we have shown is that the work you do pushing the left-hand piston down is equal to the work done by the right-hand piston as it pushes upward. Just as when we discussed simple machines in <mark>Chapter 4</mark>, we can't cheat when it comes to work. True, we can do the same job with less force, but we will always pay for that by having to exert that smaller force through a greater distance. This is the whole idea behind all simple machines, not just a hydraulic jack.

# <span style="color: #76923C">Surface Tension</span>

To complete our section on fluids at rest, we introduce the phenomenon of **surface tension**. We have all seen long-legged bugs that can walk on the surface of a pond or have watched a slowly-leaking faucet form a drop of water that grows until it finally drops into the sink. Both of these are illustrations of surface tension. The surface of a fluid can behave like an elastic membrane or thin sheet of rubber. A liquid will form a drop because the surface tends to contract into a sphere (to minimize surface area); however, when you see a drop hanging precariously from a faucet, its spherical shape is distorted by the pull of gravity. In fact, the reason it eventually falls into the sink is that the force due to surface tension causing the drop to cling to the head of the faucet is overwhelmed by the increasing weight of the drop. It can't hang on, and away it goes.

A standard way to define the surface tension is as follows. Imagine a rectangular loop of thin wire with one side able to slide up and down freely, thereby changing the enclosed area. If this apparatus is dipped into a fluid, a thin film will form in the enclosed area. Both the front face and the back face of the film are pulling upward on the free horizontal wire with a total upward force **F** against the wire's weight.

---

![Diagram of a thin film of liquid held in a frame with a sliding wire. The diagram shows a blue rectangular area labeled "thin film of liquid". An upward arrow within the film is labeled "Force due to surface tension". A horizontal dashed line with arrows at both ends is labeled "L". Below this is a solid black line representing a "wire that is free to slide up and down". A downward red arrow from the wire is labeled "Weight of the wire".](image)

The strength of the surface tension force depends on the particular liquid and is determined by the *coefficient of surface tension*, $\gamma$, which is the force per unit length. Since there are *two* surfaces here (the front and the back), each of which acts along a length $L$, the force $F$ due to surface tension acts along a total length of $2L$. The coefficient of surface tension is defined to be $\gamma = F / 2L$, so $F_{\text{surf tension}} = 2\gamma L$. To give you an idea of the values of $\gamma$, the surface tension coefficient of water is $0.07 \text{ N/m}$ at room temperature (and decreases as the temperature increases). A fluid with one of the highest surface tension coefficients is mercury. Its surface tension coefficient is nearly seven times greater than that of water: $\gamma_{\text{Hg}} = 0.46 \text{ N/m}$ at room temperature. Note that these values are really quite small. The surface of a pond of water can support the weight of a bug, but a frog isn't about to walk across the pond supported by surface tension.

---

# 8.2 HYDRODYNAMICS: FLUIDS IN MOTION

## Flow Rate and the Continuity Equation

Consider a pipe through which fluid is flowing. The **flow rate**, $f$, is the volume of fluid that passes a particular point per unit time, like how many liters of water per minute are coming out of a faucet. In SI units, flow rate is expressed in m<sup>3</sup>/s. To find the flow rate, all we need to do is multiply the cross-sectional area of the pipe at any point, $A$, by the average speed of the flow, $v$, at that point:

> ### Flow Rate
> $$f = Av$$

Be careful not to confuse flow rate with flow speed; flow rate tells us how *much* fluid flows per unit time; flow speed tells us how *fast* the fluid moves. There's a difference between saying that a hose ejects 4 liters of water every second (that's flow rate) and saying that the water leaves the hose at a speed of 4 m/s (that's flow speed).

If a pipe is carrying a liquid, which we assume is **incompressible** (that is, its density remains constant), then the flow rate must be the same everywhere along the pipe. Choose any two points in a flow tube carrying a liquid, Point 1 and Point 2. If there aren't any sources or sinks between these points (i.e., no leaks and no additional liquid), then the liquid that flows by Point 1 must also flow by Point 2, and vice versa. In other words, $f_1 = f_2$, or, since $f = Av$, we get $A_1v_1 = A_2v_2$; this is called the

> ### Continuity Equation
> $$A_1v_1 = A_2v_2$$

This tells us that when the tube narrows, the flow speed will increase; and if the tube widens, the flow speed will decrease. In fact, we can say that the flow speed is inversely proportional to the cross-sectional area (or to the square of the radius) of the pipe.

---



## Example 8-12

**Diagram Description:** A pipe with varying cross-sectional areas is shown. At Point 1 (A₁), the pipe is narrower with flow velocity v₁. At Point 2 (A₂), the pipe is wider with flow velocity v₂. The diagram illustrates that since the tube is narrower at Point 1, the flow speed is faster here, and the flow speed is slower at Point 2.

**Problem:** In the pipe shown above, if $$A_2 = 9A_1$$, then which of the following will be true?

**Answer Choices:**

A. $$v_1 = 9v_2$$

B. $$v_1 = 3v_2$$

C. $$v_2 = 9v_1$$

D. $$v_2 = 3v_1$$

**Solution:** If the cross-sectional area at Point 2 is 9 times the cross-sectional area at Point 1, then the flow speed at Point 2 will be 1/9 the flow speed at Point 1. That is, $$v_2 = v_1 / 9$$, or, solving for $$v_1$$, we get $$v_1 = 9v_2$$ (choice A).

----

## Example 8-13

**Problem:** Before using a hypodermic needle to inject medication into a patient, a nurse tests the needle by shooting a small amount of the liquid into the air. The barrel of the needle is 1 cm in diameter, and the tip is 1 mm in diameter. If the nurse pushes the piston with a speed of 2 cm/s, how fast does the liquid come out the tip?

**Answer Choices:**

A. 4 cm/s

B. 20 cm/s

C. 40 cm/s

D. 200 cm/s

**Solution:** Cross-sectional area is proportional to the square of the diameter of the flow tube. In this case, the diameter decreases by a factor of 10 (from 1 cm to 1 mm), so the cross-sectional area decreases by a factor of $$10^2 = 100$$. Now, according to the

---

continuity equation, if $A$ decreases by a factor of 100, then $v$ increases by a factor of 100. Therefore, the speed of the liquid coming out of the tip is $100 \times (2\text{ cm/s}) = 200\text{ cm/s}$, choice D.

**Example 8-14:** A pipe of nonuniform diameter carries water. At one point in the pipe, the radius is 2 cm and the flow speed is 6 m/s.

a) What's the flow rate?
b) What's the flow speed at a point where the pipe constricts to a radius of 1 cm?

**Solution:**

a) At any point, the flow rate, $f$, is equal to the cross-sectional area of the pipe multiplied by the flow speed; therefore,
$$f = Av = \pi r^2 v = \pi(2 \times 10^{-2}\text{ m})^2 (6\text{ m/s}) \approx 75 \times 10^{-4}\text{ m}^3\text{/s} = 7.5 \times 10^{-3}\text{ m}^3\text{/s}$$

b) By the continuity equation, we know that $v$, the flow speed, is inversely proportional to $A$, the cross-sectional area of the pipe. If the pipe's radius decreases by a factor of 2 (from 2 cm to 1 cm), $A$ decreases by a factor of 4 because $A$ is proportional to $r^2$. If $A$ decreases by a factor of 4, then $v$ will increase by a factor of 4. So, the flow speed at a point where the pipe's radius is 1 cm will be $4 \times (6\text{ m/s}) = 24\text{ m/s}$.

# <mark><font color="#76923c">Bernoulli's Equation</font></mark>

The most important equation in fluid dynamics is Bernoulli's equation, but before we state it, it's important to know under what conditions it applies. Bernoulli's equation applies to **ideal fluid** flow. A fluid must satisfy the following four requirements in order to be considered an ideal fluid:

*   *<font color="#76923c">The fluid is incompressible.</font>*
    This works very well for liquids; gases are quite compressible, but it turns out that we can use the Bernoulli equation for gases provided the pressure changes are small.
*   *<font color="#76923c">There is negligible viscosity.</font>*
    Viscosity is the force of cohesion between molecules in a fluid; think of it as internal friction for fluids. For example, maple syrup is more viscous than water, and there's more resistance to a flow of maple syrup than to a flow of water. (While Bernoulli's equation gives good results when applied to a flow of water, it would not give good results if it were applied to a flow of maple syrup.)
*   *<font color="#76923c">The flow is laminar.</font>*

---

In a tube carrying a flowing fluid, a *streamline* is just what it sounds like: a "line" in the stream. If we were to inject a drop of dye into a clear glass pipe carrying, say, water, we'd see a streak of dye in the pipe, indicating a streamline. The entire flow is called streamline (as an adjective) or laminar if the individual streamlines don't cross. When the flow is laminar, the fluid flows *smoothly* through the tube.

![Diagram of a curved tube showing parallel blue lines with arrows indicating the direction of fluid flow, labeled as streamlines.](image)

**streamlines**

The opposite of streamline flow is called **turbulent flow**. In this case, the flow is not smooth; it is chaotic (unpredictable). Turbulence is characterized by whirlpools and swirls (vortexes). At high enough speeds, all real fluids experience turbulent flow, and no simple equation can be applied to such a flow.

*   <mark>*The flow rate is steady.*</mark>
    That is, the value of $f$ is constant. If we're analyzing the water flowing through a garden hose connected to a faucet sticking out of the side of the house, turn the faucet handle to a particular setting and then leave it there. The flow rate through the hose must be steady while we're taking our measurements.

If these conditions hold—(1) the fluid is incompressible, (2) the flow is smooth (laminar), (3) there's no friction (viscosity), and (4) the flow rate is steady—then total mechanical energy will be conserved. *Bernoulli's equation is the statement of conservation of total mechanical energy for ideal fluid flow.* On the MCAT, you will often be told to consider a fluid to be ideal, allowing you to use Bernoulli's equation.

---

# <mark>Bernoulli's Equation</mark>

$$ p_1 + \frac{1}{2} \rho v_1^2 + \rho g y_1 = P_2 + \frac{1}{2} \rho v_2^2 + \rho g y_2 $$

In this equation, $\rho$ is the density of the flowing fluid, $P_1$ and $P_2$ give the pressures at any two points along a streamline within the flow, $v_1$ and $v_2$ give the flow speeds at these points, and $y_1$ and $y_2$ give the heights of these points above some chosen horizontal reference level.

![Diagram of a fluid flowing through a pipe that increases in elevation. Two points are marked: Point 1 at height y1 with pressure P1 and velocity v1, and Point 2 at height y2 with pressure P2 and velocity v2. Both heights are measured from a horizontal reference level.](image)

Although the equation may look complicated, notice that the two sides are the same, except all the subscripts on the left-hand side are 1's while all the subscripts on the right-hand side are 2's. Also, each $\frac{1}{2} \rho v_1^2$ term looks very much like the kinetic energy (sometimes it's referred to as kinetic energy density), and each term $\rho g y$ looks very much like gravitational potential energy. So, just take the equation you already know for conservation of total mechanical energy, $KE_1 + PE_1 = KE_2 + PE_2$, change the $m$'s to $\rho$ r's, add $P$ to both sides, and you've got Bernoulli's equation.

---

![Diagram showing a pump connected to a pipe that curves upwards. Point 1 is located just after the pump. The pipe narrows as it reaches the exit point, which is at a height y above Point 1. Water is shown exiting the pipe.](image)

**Example 8-15:** In the figure above, a pump forces water at a constant flow rate through a pipe whose cross-sectional area, $A$, gradually decreases. At the exit point, $A$ has decreased to $1/3$ its value at the beginning of the pipe. If $y = 60\text{ cm}$ and the flow speed of the water just after it leaves the pump (Point 1 in the figure) is $1\text{ m/s}$, what is the gauge pressure at Point 1?

**Solution:** We'll apply Bernoulli's equation to Point 1 and the exit point, which we'll call Point 2. We'll choose the level of Point 1 as our horizontal reference level; this makes $y_1 = 0$. Now, because the cross-sectional area of the pipe decreases by a factor of 3 between Points 1 and 2, the flow speed must increase by a factor of 3; that is, $v_2 = 3v_1$. Since the pressure at Point 2 is $P_{\text{atm}}$, Bernoulli's equation becomes

$$P_1 + \frac{1}{2} \rho v_1^2 = P_{\text{atm}} + \frac{1}{2} \rho v_2^2 + \rho g y_2$$

This tells us that

$$\begin{aligned} P_1 - P_{\text{atm}} &= \rho g y_2 + \frac{1}{2} \rho v_2^2 - \frac{1}{2} \rho v_1^2 \\ &= \rho g y_2 + \frac{1}{2} \rho (3v_1)^2 - \frac{1}{2} \rho v_1^2 \\ &= \rho (g y_2 + 4v_1^2) \\ &= (1000 \text{ kg/m}^3) [(10 \text{ m/s}^2)(0.6 \text{ m}) + 4(1 \text{ m/s})^2] \end{aligned}$$

$$\therefore P_{\text{gauge at 1}} = 10^4 \text{ Pa}$$

---

Imagine that we punch a small hole in the side of a tank of liquid. We can use Bernoulli's equation to figure out the *efflux speed*, that is, how fast the liquid will flow out of the hole.

![A diagram showing a tank of liquid with Point 1 at the top surface and Point 2 at a hole in the side. The height of Point 1 is $y_1$, the height of Point 2 is $y_2$, and the difference in height is $D = y_1 - y_2$. Liquid is shown flowing out of the hole at Point 2.](image)

Let the bottom of the tank be our horizontal reference level, and choose Point 1 to be at the surface of the liquid and Point 2 to be at the hole where the water shoots out. First, the pressure at Point 1 is at atmospheric pressure; and the emerging stream at Point 2 is open to the air, so it's at atmospheric pressure, too. Therefore, $P_1 = P_2$, and these terms cancel out of Bernoulli's equation. Next, since the area at Point 1 is so much greater than at Point 2, we can assume that $v_1$, the speed at which the water level in the tank drops, is much lower than $v_2$, the speed at which the water shoots out of the hole. (Remember that by the continuity equation, $A_1v_1 = A_2v_2$; since $A_1 >> A_2$, we'll have $v_1 << v_2$.) Because $v_1 << v_2$, we can say that $v_1 \approx 0$ and ignore $v_1$ in this case. So, Bernoulli's equation becomes

$$\rho gy_1 = \frac{1}{2} \rho v_2^2 + \rho gy_2$$

Crossing out the $\rho$'s, and rearranging, we get

$$\begin{aligned} \frac{1}{2} v_2^2 &= g(y_1 - y_2) \\ &= gD \\ v_2 &= \sqrt{2gD} \end{aligned}$$

---

That is, $v_{\text{efflux}} = \sqrt{2gD}$, where $D$ is the distance from the surface of the liquid down to the hole. This is called **Torricelli's result**. This equation should look familiar; it's basically the same formula that tells us how fast an object is going after it has fallen a distance $h$ from rest.

**Example 8-16:** The side of an above-ground pool is punctured, and water gushes out through the hole. If the total depth of the pool is 2.5 m, and the puncture is 1 m above ground level, what is the efflux speed of the water?

**Solution:** We apply Torricelli's result, $v = \sqrt{2gD}$, where $D$ is the distance from the surface of the pool down to the hole. If the puncture is 1 m above ground level, then it's $2.5 - 1 = 1.5 \text{ m}$ below the surface of the water (because the pool is 2.5 m deep). Therefore, the efflux speed will be

$$v = \sqrt{2gD} = \sqrt{2(10 \text{ m/s}^2)(1.5 \text{ m})} = \sqrt{30 \text{ m/s}^2} \approx 5.5 \text{ m/s}$$

**Example 8-17:** A hole is opened at the bottom of a full barrel of liquid. When the efflux speed has decreased to 1/2 the initial efflux speed, the barrel is:

A. 1/4 full
B. $1/\sqrt{2}$ full
C. 1/2 full
D. 3/4 full

**Solution:** Torricelli's result tells us that the efflux speed is proportional to the square root of the height to the surface of the liquid in the barrel: $v \propto \sqrt{D}$. So, if $v$ decreases by a factor of 2, then $D$ has decreased by a factor of 4, and the answer is A.

**Example 8-18:** What does Bernoulli's equation tell us about a fluid at rest in a container open to the atmosphere?

**Solution:** Consider the figure below:

---

![Diagram of a tank filled with liquid. Point 1 is at the surface, and Point 2 is at a depth D below the surface. The height of Point 1 from a reference level is $y_1$, and the height of Point 2 is $y_2$. The liquid has density $\rho$.](image)

Because the fluid in the tank is at rest, both $v_1$ and $v_2$ are zero, and Bernoulli's equation becomes

$$P_1 + \rho g y_1 = P_2 + \rho g y_2$$

Since $P_1 = P_{\text{atm}}$, if we solve this equation for $P_2$, we get

$$P_2 = P_{\text{atm}} + \rho g(y_1 - y_2) = P_{\text{atm}} + \rho g D$$

which is the same formula we found earlier for hydrostatic pressure.

## <mark>The Bernoulli Effect</mark>

Consider the two points labeled in the pipe shown below:

![Diagram of a pipe narrowing from a larger cross-sectional area $A_1$ to a smaller area $A_2$. Streamlines show fluid flow from left to right. At Point 1 (wide section), $A_1$ is large and $v_1$ is slow. At Point 2 (narrow section), $A_2$ is small and $v_2$ is fast. Both points are at heights $y_1$ and $y_2$ from a reference level.](image)

---

Since the heights $y_1$ and $y_2$ are equal in this case, the terms in Bernoulli's equation that involve the heights will cancel, leaving us with

$$P_1 + \frac{1}{2} \rho v_1^2 = P_2 + \frac{1}{2} \rho v_2^2$$

We already know from the continuity equation ($f = Av$) that the speed increases as the cross-sectional area of the pipe decreases. Since $A_2 > A_1$, we know that $v_2 < v_1$, and the equation above then tells us that $P_2 > P_1$. That is,

*The pressure is lower where the flow speed is greater.*

This is known as the **Bernoulli** (or **Venturi**) **effect**.

You may have seen a skydiver or motorcycle rider wearing a jacket that seems to puff out as they move rapidly through the air. The essentially stagnant air trapped inside the jacket is at a much higher pressure than the air whizzing by outside, and as a result, the jacket expands outward.

The drastic drop in air pressure that accompanies the high winds in a hurricane or tornado is another example. In fact, if high winds streak across the roof of a home whose windows are closed, the outside air pressure is reduced so much that the air pressure inside the house (where the air speed is essentially zero) can be great enough to blow the roof off.

**Example 8-19:** A pipe of constant cross-sectional area carries water at a constant flow rate from the hot-water tank in the basement of a house up to the second floor. Which of the following will be true?

A. The speed at which the water arrives at the second floor must be lower than the speed at which it left the water tank.
B. The speed at which the water arrives at the second floor must be greater than the speed at which it left the water tank.
C. The water pressure at the second floor must be lower than the water pressure at the tank.
D. The water pressure at the second floor must be greater than the water pressure at the tank.

**Solution:** Because the flow rate is constant and the cross-sectional area of the pipe is constant, the flow speed will be constant (this follows from the continuity equation, $f = Av = \text{constant}$). This eliminates choices A and B. Now, if the flow speeds $v_1$ and $v_2$ are the same, Bernoulli's equation becomes

---



$$P_1 + \rho g y_1 = P_2 + \rho g y_2$$

Because $y_2 > y_1$, it must be true that $P_2 < P_1$ (choice C).

